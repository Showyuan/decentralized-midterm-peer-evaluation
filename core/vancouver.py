#!/usr/bin/python
# Copyright Luca de Alfaro, 2013. 

import numpy as np
import unittest


# 是否對評分進行去偏差處理？
DEBIAS = False
# 使用中位數聚合？通常不是好主意。
AGGREGATE_BY_MEDIAN = False
# 基本精度，以標準差的倍數表示。
BASIC_PRECISION = 0.0001
# 是否使用頂點自身的數據來向該頂點發送訊息？
USE_ALL_DATA = True

class User:
    
    def __init__(self, name):
        """初始化使用者。"""
        self.name = name
        self.items = set()
        self.grade = {}
        
    def add_item(self, it, grade):
        self.items = self.items | set([it])
        self.grade[it] = grade
        

class Item:
    
    def __init__(self, id):
        self.id = id
        self.users = set()
        self.grade = None
    
    def add_user(self, u):
        self.users = self.users | set([u])


class Graph:
    
    def __init__(self, basic_precision=BASIC_PRECISION, use_all_data=USE_ALL_DATA):
        
        self.items = set()
        self.users = set()
        self.user_dict = {}
        self.item_dict = {}
        self.basic_precision = basic_precision
        self.use_all_data = use_all_data
        
    def add_review(self, username, item_id, grade):
        # 取得或建立使用者。
        if username in self.user_dict:
            u = self.user_dict[username]
        else:
            u = User(username)
            self.user_dict[username] = u
            self.users = self.users | set([u])
        # 取得或建立項目。
        if item_id in self.item_dict:
            it = self.item_dict[item_id]
        else:
            it = Item(item_id)
            self.item_dict[item_id] = it
            self.items = self.items | set([it])
        # 新增兩者之間的連接。
        u.add_item(it, grade)
        it.add_user(u)
        
    def get_user(self, username):
        return self.user_dict.get(username)
    
    def get_item(self, item_id):
        return self.item_dict.get(item_id)
    
    def evaluate_items(self, n_iterations=20):
        """使用聲譽系統迭代來評估項目。"""
        # 建立從使用者到項目的初始訊息。
        for it in self.items:
            it.msgs = []
            for u in it.users:
                m = Msg()
                m.user = u
                m.grade = u.grade[it]
                m.variance = 1.0
                it.msgs.append(m)
        # 執行傳播迭代。
        for i in range(n_iterations):
            self._propagate_from_items()
            self._propagate_from_users()
        # 執行最終的聚合步驟。
        self._aggregate_item_messages()
        self._aggregate_user_messages()


    # 使用平均投票評估每個項目。
    def avg_evaluate_items(self):
        item_value = {}
        for it in self.items:
            grades = []
            for u in it.users:
                grades.append(u.grade[it])
            it.grade = aggregate(grades)
            
    
    def _propagate_from_items(self):
        """從項目向使用者傳播資訊。"""
        # 首先，清除所有傳入的訊息。
        for u in self.users:
            u.msgs = []
        # 對於每個項目，向使用者提供回饋。
        for it in self.items:
            # 對於評估過該項目的每個使用者，向該使用者報告以下
            # 從其他使用者計算得出的數量：
            # 平均值/中位數
            # 標準差
            # 總權重
            for u in it.users:
                if len(it.msgs) > 0:
                    grades = []
                    variances = []
                    for m in it.msgs:
                        if self.use_all_data or m.user != u or len(it.msgs) < 2:
                            grades.append(m.grade)
                            variances.append(m.variance)
                    variances = np.array(variances)
                    weights = 1.0 / (self.basic_precision + variances)
                    weights /= np.sum(weights)
                    msg = Msg()
                    msg.item = it
                    msg.grade = aggregate(grades, weights=weights)
                    # 現在我需要估計分數的標準差。
                    msg.variance = np.sum(variances * weights * weights)
                    u.msgs.append(msg)
    
    
    def _propagate_from_users(self):
        """從使用者向項目傳播資訊。"""
        # 首先，清除項目中接收到的訊息。
        for it in self.items:
            it.msgs = []
        # 從使用者向項目發送資訊。
        # 要發送的資訊是評分和估計的標準差。
        for u in self.users:
            for it in u.items:
                if len(u.msgs) > 0:
                    # 使用者查看來自其他項目的訊息，並計算
                    # 其評估的偏差。
                    msg = Msg()
                    msg.user = u
                    biases = []
                    weights = []
                    if DEBIAS:
                        for m in u.msgs:
                            if self.use_all_data or m.item != it or len(u.msgs) < 2:
                                weights.append(1 / (self.basic_precision + m.variance))
                                given_grade = u.grade[m.item]
                                other_grade = m.grade
                                biases.append(given_grade - other_grade)
                        u.bias = aggregate(biases, weights=weights)
                    else:
                        u.bias = 0.0
                    # 評分是給定的評分，經過去偏差處理。
                    msg.grade = u.grade[it] - u.bias
                    # 從其他已判斷的項目估計使用者的標準差。
                    variance_estimates = []
                    weights = []
                    for m in u.msgs:
                        if self.use_all_data or m.item != it or len(u.msgs) < 2:
                            it_grade = u.grade[m.item] - u.bias
                            variance_estimates.append((it_grade - m.grade) ** 2.0)
                            weights.append(1.0 / (self.basic_precision + m.variance))
                    msg.variance = aggregate(variance_estimates, weights=weights)
                    # 訊息準備好排入佇列。
                    it.msgs.append(msg)
                    
    
    def _aggregate_item_messages(self):
        """聚合項目上的資訊，計算評分
        和評分的變異數。"""
        for it in self.items:
            it.grade = None
            it.variance = None
            if len(it.msgs) > 0:
                grades = []
                variances = []
                for m in it.msgs:
                    grades.append(m.grade)
                    variances.append(m.variance)
                variances = np.array(variances)
                weights = 1.0 / (self.basic_precision + variances)
                weights /= np.sum(weights)
                it.grade = aggregate(grades, weights=weights)
                it.variance = np.sum(variances * weights * weights)
    
    
    def _aggregate_user_messages(self):
        """聚合使用者上的資訊，計算使用者的
        變異數和偏差。"""
        for u in self.users:
            u.variance = None
            if len(u.msgs) > 0:
                biases = []
                weights = []
                # 估計偏差。
                if DEBIAS:
                    for m in u.msgs:
                        weights.append(1 / (self.basic_precision + m.variance))
                        given_grade = u.grade[m.item]
                        other_grade = m.grade
                        biases.append(given_grade - other_grade)
                    u.bias = aggregate(biases, weights=weights)
                else:
                    u.bias = 0.0
                # 估計每個項目的評分。
                variance_estimates = []
                weights = []
                for m in u.msgs:
                    it_grade = u.grade[m.item] - u.bias
                    variance_estimates.append((it_grade - m.item.grade) ** 2.0)
                    weights.append(1.0 / (self.basic_precision + m.variance))
                u.variance = aggregate(variance_estimates, weights=weights)
            
            
    def evaluate_users(self):
        """透過比較使用者的變異數與隨機給分的變異數來評估使用者。"""
        # 計算所有給定評分的標準差。
        all_grades = []
        for u in self.users:
            all_grades.extend(u.grade.values())
        overall_stdev = np.std(all_grades)
        # 兩個數字差值的標準差是數字標準差的 sqrt(2) 倍，
        # 假設為常態分佈。
        overall_stdev *= 2 ** 0.5
        for u in self.users:
            u.quality = max(0.0, 1.0 - (u.variance ** 0.5) / overall_stdev)


    def avg_evaluate_users(self):
        """從項目評分評估使用者，就像沒有實際發送訊息一樣。"""
        # 計算所有給定評分的標準差。
        all_grades = []
        for u in self.users:
            all_grades.extend(u.grade.values())
        overall_stdev = np.std(all_grades)
        # 兩個數字差值的標準差是數字標準差的 sqrt(2) 倍，
        # 假設為常態分佈。
        overall_stdev *= 2 ** 0.5
        for u in self.users:
            diffs = []
            for it in u.items:
                d = it.grade - u.grade[it]
                diffs.append(d * d)
            u.variance = np.average(diffs)
            u.quality = max(0.0, 1.0 - (u.variance ** 0.5) / overall_stdev)


class Msg():
    def __init__(self):
        pass


def aggregate(v, weights=None):
    """使用平均值或中位數進行聚合。"""
    if AGGREGATE_BY_MEDIAN:
        if weights is not None:
            return median_aggregate(v, weights=weights)
        else:
            return median_aggregate(v)
    else:
        if weights is not None:
            return np.average(v, weights=weights)
        else:
            return np.average(v)


def median_aggregate(values, weights=None):
    if len(values) == 1:
        return values[0]
    if weights is None:
        weights = np.ones(len(values))
    # 排序。
    vv = []
    for i in range(len(values)):
        if weights[i] > 0:
            vv.append((values[i], weights[i]))
    if len(vv) == 0:
        return values[0]
    if len(vv) == 1:
        x, _ = vv[0]
        return x
    vv.sort()
    v = np.array([x for x, _ in vv])
    w = np.array([y for _, y in vv])
    # print 'v', v, 'w', w
    # 此時，數值已排序，都有非零權重，
    # 且至少有兩個數值。
    half = np.sum(w) / 2.0
    below = 0.0
    i = 0
    while i < len(v) and below + w[i] < half:
        below += w[i]
        i += 1
    # print 'i', i, 'half', half, 'below', below
    if half < below + 0.5 * w[i]:
        # print 'below'
        if i == 0:
            return v[0]
        else:
            alpha = half - below
            beta = below + 0.5 * w[i] - half
            # print 'alpha', alpha, 'beta', beta
            return (beta * (v[i] + v[i - 1]) / 2.0 + alpha * v[i]) / (alpha + beta)
    else:
        # print 'above'
        if i == len(v) - 1:
            # print 'last'
            return v[i]
        else:
            alpha = half - below - 0.5 * w[i]
            beta = below + w[i] - half
            # print 'alpha', alpha, 'beta', beta
            return (beta * v[i] + alpha * (v[i] + v[i + 1]) / 2.0) / (alpha + beta)


class TestMedian(unittest.TestCase):
    
    def test_median_0(self):
        values = [1.0, 3.0, 2.0]
        weights = [1.0, 1.0, 1.0]
        m = median_aggregate(values, weights=weights)
        self.assertAlmostEqual(m, 2.0, 4)

    def test_median_1(self):
        values = [1.0, 3.0, 2.0]
        weights = [1.0, 1.0, 2.0]
        m = median_aggregate(values, weights=weights)
        self.assertAlmostEqual(m, 2.0, 4)

    def test_median_2(self):
        values = [1.0, 3.0, 2.0]
        weights = [1.0, 2.0, 1.0]
        m = median_aggregate(values, weights=weights)
        self.assertAlmostEqual(m, 2.5, 4)

    def test_median_3(self):
        values = [1.0, 3.0, 2.0]
        weights = [1.0, 2.0, 2.0]
        m = median_aggregate(values, weights=weights)
        self.assertAlmostEqual(m, 2.25, 4)


class test_reputation(unittest.TestCase):
    
    def test_rep_1(self):
        g = Graph()
        g.add_review('luca', 'pizza', 8.0)
        g.add_review('luca', 'pasta', 9.0)
        g.add_review('luca', 'pollo', 5.0)
        g.add_review('mike', 'pizza', 7.5)
        g.add_review('mike', 'pollo', 8.0)
        g.add_review('hugo', 'pizza', 6.0)
        g.add_review('hugo', 'pasta', 7.0)
        g.add_review('hugo', 'pollo', 7.5)
        g.add_review('anna', 'pizza', 7.0)
        g.add_review('anna', 'pasta', 8.5)
        g.add_review('anna', 'pollo', 5.5)
        g.add_review('carl', 'pollo', 5.4)
        g.add_review('luca', 'steak', 6.0)
        g.evaluate_items()
        print('pasta', g.get_item('pasta').grade)
        print('pizza', g.get_item('pizza').grade)
        print('pollo', g.get_item('pollo').grade)
        print('variances:')
        print('luca', g.get_user('luca').variance)
        print('mike', g.get_user('mike').variance)
        print('hugo', g.get_user('hugo').variance)
        print('anna', g.get_user('anna').variance)
        print('qualities:')
        g.evaluate_users()
        print('luca', g.get_user('luca').quality)
        print('mike', g.get_user('mike').quality)
        print('hugo', g.get_user('hugo').quality)
        print('anna', g.get_user('anna').quality)

if __name__ == '__main__':
    unittest.main()
    pass
