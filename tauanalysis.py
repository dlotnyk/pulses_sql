"""
Created on Mon Dec  3 11:05:06 2018

@author: dlotnyk
"""
# -*- coding: utf-8 -*-
import sys
from createdata import calltracker
from createdata import my_logger
from createdata import time_this
from createdata import sql_create as sqdata
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as ss
import warnings
warnings.simplefilter('ignore', np.RankWarning)
sys.path.insert(0, 'e:\\repos\\')
from configa import conf
# -------------------------------------


class timetotemp(sqdata):
    vals = ['time', 'Q', 'Tmc', 'index', 'pulse']  # the most important columns
    plimit = 1500  # value in Q which identify the pulsing
    callme = True
    # list of Tc for experiments
    tc = {'0bar': 0.929, '9psi': 1.013, '22bar': 2.293}
# ---------------------------------------------------------

    def __init__(self, conf, sett):
        '''connect to conn mysql server with data'''
        self.maxvaluecall = False
        self.conf = conf
        self.sett = sett
        self.title = sett['pressure']
        self.connect_f(conf)
        assert self.sett['indent'] >= 0, "cut from begin. it should be > 0"
        assert self.sett['cut'] > self.sett['indent'] >= 0, "cut always greater than indent"
        assert self.sett['offset'] >= 0, "offset it should be > 0"
# ---------------------------------------------------------

    def __repr__(self):
        return str(self.__class__.__name__)+" "+str(self.sett['pressure'])+", db: "+str(self.conf['database'])

# -----------------------------------------------------------
    @my_logger
    @time_this
    def import_fun(self):
        '''select time,Q and Tmc data from database. slice later. could be improved with BETWEEN'''
        data1 = self.select_col(
            self.vals, self.tables[self.sett['pressure']][0])
        data2 = self.select_col(
            self.vals, self.tables[self.sett['pressure']][1])
        a = np.shape(data1)[0]
        b = str(a)
        # value grater than index. starting point for new pulsing data
        self.mval = round(a, -len(b)+1)+10**(len(b)-1)
        data11 = data1[self.sett['indent']:self.sett['cut'], :]
        data21 = data2[self.sett['indent']:self.sett['cut'], :]
#        data2=data2[0:-self.sett['offset'],:]
        data13 = np.transpose(data11)
        data23 = np.transpose(data21)
        t0 = data23[0][0]
        data13[0] = data13[0]-t0
        data23[0] = data23[0]-t0
        return data13, data23
# ---------------------------------------------------------
    @my_logger
    @time_this
    def pulse_indicies(self, data1, data2):
        '''Find pulses in IC fork'''
        a = np.where(np.abs(data2[1]) > self.plimit)
        pulse = []
        pulse.append(a[0][0])
        ite = a[0][0]
        for x in range(1, np.shape(a)[1]):
            if (a[0][x] > ite+100):
                pulse.append(a[0][x])
                ite = a[0][x]
            else:
                ite += 1
        pul = np.asarray(pulse)
        return pul
# ---------------------------------------------------------
    @my_logger
    @time_this
    def pulse_renumb(self, data2):
        '''renumber of pulses and update in sql. start from mval and 1000 per each pulse'''

        ini = self.mval
        pul_id = 0
        id1 = 0
        id2 = self.pulse_id[0]
        increm = 1000/(id2-id1)
        count = 0
        nump = 1
        for ii in data2[3]:
            if ii == data2[3][self.pulse_id[pul_id]]:
                pul_id += 1
                if pul_id == np.shape(self.pulse_id)[0]:
                    id1 = self.pulse_id[pul_id-1]
                    id2 = np.shape(data2)[1]
                    pul_id -= 1
                else:
                    id1 = self.pulse_id[pul_id-1]
                    id2 = self.pulse_id[pul_id]
                increm = 1000/(id2-id1)
                self.__set_pulse(
                    self.sett['indent']+count+1, self.mval+1000*nump)
                nump += 1
            else:
                self.__set_pulse(self.sett['indent']+count+1, ini)
            count += 1
            ini += increm
        self.cnx.commit()
# -----------------------------------------------------------
    @my_logger
    @time_this
    def __pulse_st(self):
        '''Find the maximum value of `pulse` during the first start'''
        tab1_count = ("SELECT COUNT(`index`) FROM `{}`".format(
            self.tables[self.sett['pressure']][0]))
        self.cursor.execute(tab1_count)
        res1 = self.cursor.fetchall()
        b = str(res1[0][0])
        # value grater than index. starting point for new pulsing data
        self.mval = round(res1[0][0], -len(b)+1)+10**(len(b)-1)
 # ---------------------------------------------------------
    @my_logger
    @time_this
    def first_start(self):
        '''command sequence of the program after creating tables in sql create class'''
        data_hec, data_ic = self.import_fun()
        self.pulse_id = self.pulse_indicies(data_hec, data_ic)
        self.pulse_renumb(data_ic)
#        self.pulse_remove2(data_hec,data_ic)
 # ---------------------------------------------------------

    def __set_pulse(self, ind, val):
        '''update a value of `pulse` in a HEC table. it is a primary key bonded with IC'''
        set_v = ("UPDATE `{0}` SET `pulse` = '{1}' WHERE `{0}`.`index` = '{2}'".format(
            self.tables[self.sett['pressure']][0], val, int(ind)))
        self.cursor.execute(set_v)

# --------------------------------------------------------------------------------------------------
    @my_logger
    @time_this
    def sel_onlypulse(self, r_list, tab):
        '''select data only with pulses i.e. 70000 and higher `pulse`'''
        if not(self.maxvaluecall):
            self.__pulse_st()
        cur = ''
        for ii in r_list:
            cur += "`"+ii+"`, "
        cur = cur[0:-2]
        query = (
            "SELECT "+cur+" FROM `{0}` WHERE `pulse` > '{1}' ORDER BY `{0}`.`index` ASC".format(tab, str(self.mval)))
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        dat = self._removeNull(res)
        dat1 = np.transpose(dat)
        self.maxvaluecall = True
        return dat1
 # ---------------------------------------------------------
    @my_logger
    @time_this
    def sel_onlypulseJoin(self, r_list1, tab1, r_list2, tab2):
        '''select data only with pulses i.e. 70000 and higher `pulse` JOIN two tables by `pulse`'''
        assert type(r_list1) is list and type(
            tab1) is str, "HEC data not list or string"
        assert type(r_list2) is list and type(
            tab2) is str, "IC data not list or string"
        if not(self.maxvaluecall):
            self.__pulse_st()
        cur1 = ''
        for ii in r_list1:
            cur1 += "`"+str(tab1)+"`.`"+ii+"`, "
        cur1 = cur1[0:-2]
        cur2 = ''
        for jj in r_list2:
            cur2 += "`"+str(tab2)+"`.`"+jj+"`, "
        cur2 = cur2[0:-2]
        query = ("SELECT "+cur1+", "+cur2 +
                 " FROM `{0}` JOIN `{1}` "
                 "ON `{0}`.`pulse` = `{1}`.`pulse` "
                 "WHERE `{0}`.`pulse` > '{2}' ORDER BY `{0}`.`index` ASC".format(tab1, tab2, str(self.mval)))
#        print(query)
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        dat = self._removeNull(res)
        dat1 = np.transpose(dat)
        self.maxvaluecall = True
        return dat1
 # ---------------------------------------------------------
    @my_logger
    @time_this
    def pulse_remove(self, n1, n2, data1, data2):
        '''Remove pulse and n1/n2-surroundings'''
        a = range(-n1, n2)
        b = np.where(np.abs(data2[1]) > self.plimit)
        s = []
        for p in np.nditer(self.pulse_id):
            for ad in np.nditer(a):
                s.append(ad+p)
        pulse_rem = np.asarray(s)
        d1 = np.in1d(range(0, len(data1[1])),
                     pulse_rem, assume_unique=True, invert=True)
        d2 = np.in1d(range(0, len(data2[1])),
                     pulse_rem, assume_unique=True, invert=True)
#        new_in=self.pulse_remove2(b)
#        print(new_in)
#        self.cnx.commit()!
        self.__remInsq(d1, b)
        self.cnx.commit()
        return d1, d2
 # ---------------------------------------------------------
    @my_logger
    @time_this
    def pulse_remove2(self, a):
        '''Remove pulse and n1/n2-surroundings'''
        new_in = -1
        for idx in a[0]:
            self.__set_pulse(self.sett['indent']+idx+2, new_in)
            new_in -= 1
        self.cnx.commit()
        return new_in

# ------------------------------------------------------------
    def __remInsq(self, d1, b):
        '''update `pulse` values in table according to removing pulse'''
        new_in = -1
        for idx, ni in enumerate(d1):
            if (ni == False) or (idx in b[0]):
                self.__set_pulse(self.sett['indent']+idx+2, new_in)
                new_in -= 1

# ------------------------------------------------------------
    @my_logger
    @time_this
    def temp_fit(self, nump):
        '''nump - polyfit regression fit of temperature data, removing nan first
        select Tmc but update Tmc/Tc in order to save original data in Tmc'''
        res = self.sel_onlypulse(
            ['time', 'Tmc', 'index'], self.tables[self.sett['pressure']][0])
        na = np.where(np.isnan(res[1]))
        sh = np.shape(res)[1]
        d1 = np.in1d(range(0, sh), na, invert=True)
        w = np.ones(sh)
        w[int(sh/2):] = 2
        fit = np.polyfit(res[0][d1], res[1][d1], nump, w=w[d1])
        fit_fn = np.poly1d(fit)
        temp2 = fit_fn(res[0])
        dt = self.tc[self.sett['pressure']] - \
            np.mean(temp2[-30:-1])  # correction to tc
        fit[-1] += dt
        temp2 = fit_fn(res[0][d1])
        fit_rev = np.polyfit(temp2, res[0][d1], nump)
        for idx, y in enumerate(fit_fn(res[0])):
            s_com1 = ("UPDATE `{0}` SET `Tmc/Tc` = '{1}' WHERE `{0}`.`index` = '{2}'".format(
                self.tables[self.sett['pressure']][0], y, res[2][idx]))
            s_com2 = ("UPDATE `{0}` SET `Tmc/Tc` = '{1}' WHERE `{0}`.`index` = '{2}'".format(
                self.tables[self.sett['pressure']][1], y, res[2][idx]))
            self.cursor.execute(s_com1)
            self.cursor.execute(s_com2)
        self.cnx.commit()
#        print(s_com1)
#        print(s_com2)
        fig1 = plt.figure(7, clear=True)
        ax1 = fig1.add_subplot(111)
        ax1.set_ylabel('T')
        ax1.set_xlabel('time')
        ax1.set_title('T and time')
        ax1.plot(res[0][d1], res[1][d1], color='green', lw=1)
        ax1.plot(res[0][d1], fit_fn(res[0][d1]), color='blue', lw=1)
        plt.grid()
        # plt.show()
        return fit, fit_rev

 # ------------------------------------------------------------
    @my_logger
    @time_this
    def QtoT(self, nump):
        '''Transformation of Q into Temperature based on HEC Fork
        nump - degree of polyfit'''
        assert type(nump) is int, "Must be integer"
        # choose updated values Tmc/Tc
        res = self.sel_onlypulse(
            ['Q', 'Tmc/Tc', 'index', 'time'], self.tables[self.sett['pressure']][0])
        filt = ss.medfilt(res[0], 21)
        w = np.ones(len(res[0]))
        w[0:100] = 15
        w[-100:-1] = 15
        fit = np.polyfit(res[1], filt, nump, w=w)  # T vs Q first
        fit_fn = np.poly1d(fit)  # Q
        Q = fit_fn(res[1])
        fit2 = np.polyfit(Q, res[1], nump, w=w)  # Q vs T fit. main one
        fit_fn2 = np.poly1d(fit2)  # T
        fig1 = plt.figure(8, clear=True)
        ax1 = fig1.add_subplot(211)
        ax1.set_ylabel('Q')
        ax1.set_xlabel('T')
        ax1.set_title('Q vs T')
        ax1.plot(res[1], res[0], color='blue', lw=1)
        ax1.plot(res[1], Q, color='red', lw=1)
        ax1.plot(res[1], filt, color='green', lw=1)
        plt.grid()
        ax2 = fig1.add_subplot(212)
        ax2.set_ylabel(r'$T/T_c$')
        ax2.set_xlabel('time')
        ax2.set_title(r'$T/T_c$ vs Q')
        ax2.plot(res[3], fit_fn2(res[0]) /
                 self.tc[self.sett['pressure']], color='blue', lw=1)
#        ax2.plot(Q,T, color='red',lw=1)
#        ax2.plot(filt,res[1], color='green',lw=1)
        plt.grid()
        # plt.show()
#        dat=np.vstack((filt,T))
        return fit2
    # ------------------------------------------------------------
    @my_logger
    @time_this
    def QtoTic(self, fit):
        '''Converts Q to temp for an IC fork using calibration from HEC'''
        fit_fn = np.poly1d(fit)
        res = self.sel_onlypulseJoin(['Q'], self.tables[self.sett['pressure']][0], [
                                     'Q', 'Tmc/Tc', 'index', 'time'], self.tables[self.sett['pressure']][1])
        # connect two datasets in the end taking into account hte offset
        Q1 = np.mean(res[1][-10:-1])
        Q2 = np.mean(res[0][-10:-1])
        dQ = Q1-Q2  # correction to Q
        tloc = fit_fn(res[1]-dQ)

        fig1 = plt.figure(9, clear=True)
        ax1 = fig1.add_subplot(111)
        ax1.set_ylabel(r'$T_{loc}$')
        ax1.set_xlabel('time')
        ax1.set_title(r'$T_{loc}$ vs time')
        ax1.plot(res[4], tloc, color='blue', lw=1)
#        ax1.plot(res[1],Q, color='red',lw=1)
#        ax1.plot(res[1],filt, color='green',lw=1)
        plt.grid()
        # plt.show()
        return dQ

 # ------------------------------------------------------------
    @my_logger
    @time_this
    def update_local(self, tab, fit, dQ):
        '''update a local temerature coloumn in sql table'''
        assert type(tab) is str, 'Table is string'
        assert type(fit) is np.ndarray, "fit is numpy.ndarray"
        fit_fn = np.poly1d(fit)
        res = self.sel_onlypulse(['Q', 'index'], tab)
        # update a SQL table
        for idx, val in enumerate(res[0]):
            self.__set_local(tab, res[1][idx], fit_fn(
                val-dQ), fit_fn(val-dQ)/self.tc[self.sett['pressure']])
        self.cnx.commit()

 # ------------------------------------------------------------
    def __set_local(self, tab, index, value1, value2):
        '''set value in the SQL table tab with index index and value1 is loc, value2 is Tloc/Tc'''
        s_com1 = ("UPDATE `{0}` SET `Tloc` = '{1}' WHERE `{0}`.`index` = '{2}'".format(
            tab, value1, index))
        s_com2 = (
            "UPDATE `{0}` SET `Tloc/Tc` = '{1}' WHERE `{0}`.`index` = '{2}'".format(tab, value2, index))
        self.cursor.execute(s_com1)
        self.cursor.execute(s_com2)
# ------------------------------------------------------------

#    @my_logger
#    @time_this
    @calltracker
    def pick_sep(self, num, nump):
        '''pick a separate pulse num. sstarts from 0'''
        assert type(num) is int and type(
            nump) is int, "both params are integers"
#        nump=20
        if not(self.maxvaluecall):
            self.__pulse_st()
        ns = str(self.mval+1000*num)
        ne = str(self.mval+1000*(num+1))
        query = ("SELECT `{0}`.`Tloc/Tc`, `{1}`.`Tloc/Tc`, `{1}`.`Tmc/Tc`"
                 " FROM `{0}` JOIN `{1}` "
                 "ON `{0}`.`pulse` = `{1}`.`pulse` "
                 "WHERE `{0}`.`pulse` BETWEEN '{2}' AND '{3}' ORDER BY `{0}`.`index` ASC".format(self.tables[self.sett['pressure']][0], self.tables[self.sett['pressure']][1], ns, ne))
#        print(query)
        self.cursor.execute(query)
        res = self.cursor.fetchall()
#        dat=self._removeNull(res)
        dat = res
        dat = dat[:][1:]
        dat1 = np.transpose(dat)
        fit = np.polyfit(dat1[1][0:nump], dat1[0][0:nump], 1)
        fig1 = plt.figure(3, clear=self.callme)
        if self.callme:
            ax1 = fig1.add_subplot(111)
            ax1.set_xlabel(r'$T_{loc}/T_c$(IC)')
            ax1.set_ylabel(r'$T_{loc}/T_c$(HEC)')
            ax1.set_title(r'$T_{loc}$ vs $T_{loc}$')
        else:
            ax1 = plt.gca()
        ax1.scatter(dat1[1][0:nump], dat1[0][0:nump], color='blue', s=2)
#        ax1.scatter(dat1[1], dat1[0], color='blue',s=2)
        plt.grid()
        # plt.show()
        self.callme = False
        if fit[0] < 0:
            fit[0] = np.nan
        ret = (fit[0], dat1[2][0]/self.tc[self.sett['pressure']])
        self.maxvaluecall = True
        return ret
# ------------------------------------------------------------
    @my_logger
    @time_this
    def loop_number(self):
        '''find a number of pulses which is identical to len(pulse_indicies)'''
        if not(self.maxvaluecall):
            self.__pulse_st()
        query = ("SELECT MAX(`{0}`.`pulse`) FROM `{0}`".format(
            self.tables[self.sett['pressure']][0]))
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        dat = round(res[0][0], -3)
        num = int((dat-self.mval)/1000)
        self.maxvaluecall = True
#        print(self.mval,dat,num)
        return num
# ------------------------------------------------------------
    @my_logger
    @time_this
    def plot_dt(self, f):
        '''plot dt/dt vs Tmc/Tc'''
        assert type(f) is list and type(
            f[0]) is tuple, "input should be a list of tuples"
        f = f[1:]
        fig2 = plt.figure(4, clear=True)
        ax1 = fig2.add_subplot(111)
        ax1.set_ylabel(r'$dT_{HEC}/dT_{IC}$')
        ax1.set_xlabel('time [sec]')
        ax1.set_title('dT/dT')
        ax1.scatter([ii[1] for ii in f], [ii[0]
                                          for ii in f], color='green', s=5)
        plt.grid()
        # plt.show()
# ------------------------------------------------------------
    @my_logger
    @time_this
    def save_dt(self, f):
        '''save into file the dt/dt vs Tmc/Tc'''
        assert type(f) is list and type(
            f[0]) is tuple, "input should be a list of tuples"
        name = "dtdt_for_"+self.sett['pressure']+'.dat'
        list1 = ["{0} \t {1} \n".format(ii[1], ii[0]) for ii in f]
        list1.insert(0, "{0} \t {1} \n".format("Tmc/Tc", "dThec/dTic"))
        str1 = ''.join(list1)
        with open(name, 'w') as file1:
            file1.write(str1)
# ------------------------------------------------------------
    @my_logger
    @time_this
    def dlocal(self, data, loopn, n_pul):
        '''calulate and plot dt over dt for single pulse
        data are time, q, T for both forks,
        loopn - number of pulses
        f1 is a dt for HEC; f2 is a dt for IC, f3 is a time
        num is a number of points in each pulse'''
        # calculate background
        n1 = 900
        n2 = 999
        n_fir = 200
        npoly = 6
        l1 = [np.mean(data[2][np.where(np.logical_and(data[4] >= self.mval+ii *
                                                      1000+n1, data[4] <= self.mval+ii*1000+n2))[0]]) for ii in range(1, loopn)]
        l2 = [np.mean(data[6][np.where(np.logical_and(data[4] >= self.mval+ii *
                                                      1000+n1, data[4] <= self.mval+ii*1000+n2))[0]]) for ii in range(1, loopn)]
        l3 = [np.mean(data[0][np.where(np.logical_and(data[4] >= self.mval+ii *
                                                      1000+n1, data[4] <= self.mval+ii*1000+n2))[0]]) for ii in range(1, loopn)]
        num = [len(np.where(np.logical_and(data[4] >= self.mval+ii*1000,
                                           data[4] <= self.mval+ii*1000+n_fir))[0]) for ii in range(1, loopn)]
        f1 = [data[2][jj] for ii in range(1, loopn) for jj in np.where(np.logical_and(
            data[4] >= self.mval+ii*1000, data[4] <= self.mval+ii*1000+n_fir))[0]]
        f2 = [data[6][jj] for ii in range(1, loopn) for jj in np.where(np.logical_and(
            data[4] >= self.mval+ii*1000, data[4] <= self.mval+ii*1000+n_fir))[0]]
        f3 = [data[0][jj] for ii in range(1, loopn) for jj in np.where(np.logical_and(
            data[4] >= self.mval+ii*1000, data[4] <= self.mval+ii*1000+n_fir))[0]]
        Tmc = [data[7][jj]/self.tc[self.sett['pressure']] for ii in range(1, loopn) for jj in np.where(
            np.logical_and(data[4] >= self.mval+ii*1000, data[4] <= self.mval+ii*1000+n_fir))[0]]

        fit = np.polyfit(l3, l1, npoly)
        fval = np.poly1d(fit)
        fit2 = np.polyfit(l3, l2, npoly)
        fval2 = np.poly1d(fit2)
        # find dt's
        for idx, (v1, v2, v3) in enumerate(zip(f1, f2, f3)):
            f1[idx] = v1 - fval(v3)
            f2[idx] = v2 - fval2(v3)
        # plotting
        fig1 = plt.figure(5, clear=True)
        ax1 = fig1.add_subplot(211)
        ax1.set_ylabel(r'$T_{loc}^{HEC}/T_c$')
        ax1.set_xlabel(r'$T_{loc}^{IC}/T_c$')
        ax1.set_title(r'$T_{loc}$ vs time for both forks')
        ax1.scatter(l3, l1, color='green', s=5)
        ax1.scatter(data[0], fval(data[0]), color='red', s=0.5)
        plt.grid()
        ax2 = fig1.add_subplot(212)
        ax2.set_ylabel(r'$T_{loc}^{HEC}/T_c$')
        ax2.set_xlabel(r'$T_{loc}^{IC}/T_c$')
        ax2.set_title(r'$T_{loc}$ vs time for both forks')
        ax2.scatter(l3, l2, color='green', s=5)
        ax2.scatter(data[0], fval2(data[0]), color='red', s=0.5)
        plt.grid()
        # plt.show()
        fig3 = plt.figure(6, clear=True)
        ax3 = fig3.add_subplot(111)
        ax3.set_ylabel(r'$\Delta T_{HEC}/T_c$')
        ax3.set_xlabel(r'$\Delta T_{IC}/T_c$')
        ax3.set_title(r'$\Delta$`s for '+self.sett['pressure'])
#        ax1.scatter(dt2,dt1,color='green', s=5)
        ax3.set_prop_cycle(
            color=['red', 'green', 'blue', 'black', 'cyan', 'magenta', 'orange'])
        c1 = 0
        for ii in range(n_pul):
            c2 = c1+num[ii]
            ax3.scatter(f2[c1:c2], f1[c1:c2], lw=3, label=str(ii+1))
            c1 = c2

#        ax1.scatter(data[0],fval(data[0]),color='red', s=0.5)
        ax3.legend()
        plt.grid()
        # plt.show()
        return f1, f2, f3, num, Tmc
# ------------------------------------------------------------
    @my_logger
    @time_this
    def dpart(self, f1, f2, f3, num, n_pul, Tmc):
        '''analysis of pulses found in dlocal method
        f1 is a dt for HEC; f2 is a dt for IC, f3 is a time
        num is a number of points in each pulse
        n_pul is a number of pulses we want to show'''
        cut = 0.25  # 15 % to cut
        c1 = 0
        fig1 = plt.figure(7, clear=True)
        ax1 = fig1.add_subplot(211)
        ax1.set_ylabel(r'$\Delta T_{HEC}/T_c$')
        ax1.set_xlabel(r'$\Delta T_{IC}/T_c$')
        ax1.set_title(r'$\Delta$`s for '+self.sett['pressure'])
#        ax1.scatter(dt2,dt1,color='green', s=5)
        ax1.set_prop_cycle(
            color=['red', 'green', 'blue', 'black', 'cyan', 'magenta', 'orange'])
        slopes = np.zeros(n_pul)
        temp = np.zeros(n_pul)
        for ii in range(n_pul):
            c2 = c1+num[ii]
            x1 = np.asarray(f1[c1:c2])
            x2 = np.asarray(f2[c1:c2])
            ma = np.amax(x1)
            mi = np.amin(x1)
            if self.sett['pressure'] == '0bar':
                valcut = ma-cut*(ma-mi)  # 0bar
            else:
                valcut = mi+cut*(ma-mi)  # 9psi and 22 bar
#                valcut=ma-cut*(ma-mi) # 0bar

            ind = np.where(x1 <= valcut)
            ax1.scatter(x2[ind], x1[ind], lw=3, label=str(ii+1))
            fit = np.polyfit(x2[ind], x1[ind], 1)
            temp[ii] = np.mean(Tmc[c1:c2])
            if fit[0] < 0:
                slopes[ii] = np.nan
            else:
                slopes[ii] = fit[0]
            c1 = c2
#        ax1.legend()
        plt.grid()
        ax2 = fig1.add_subplot(212)
        ax2.set_ylabel(r'$\Delta T_{HEC}/\Delta T_{IC}$')
        ax2.set_xlabel(r'time will do the temperature')
        ax2.scatter(temp, slopes, lw=3, label=str(ii+1))
        plt.grid()
        self.saveslopes(slopes, temp)
        return slopes
# ------------------------------------------------------------
    @my_logger
    @time_this
    def saveslopes(self, slopes, Tmc):
        '''save slopes into file'''
        name = "slopes_for_"+self.sett['pressure']+'.dat'
        list1 = ["{0} \t {1} \n".format(jj, ii) for ii, jj in zip(slopes, Tmc)]
        list1.insert(0, "{0} \t {1} \n".format("Tmc/Tc", "dThec/dTic"))
        str1 = ''.join(list1)
        with open(name, 'w') as file1:
            file1.write(str1)


# main program below------------------------------------------------------------------------
if __name__ == '__main__':
    sett1 = {'pressure': '0bar', 'indent': 9200, 'cut': 47000, 'offset': 1800
             }
    sett2 = {'pressure': '9psi', 'indent': 10000, 'cut': 53000, 'offset': 700
             }
    sett3 = {'pressure': '22bar', 'indent': 1000, 'cut': 41000, 'offset': 1
             }
    toplot = False
    A = timetotemp(conf, sett3)
#    A.first_start()
#    data1=A.sel_onlypulse(['time','Q','Tmc','index','pulse'],A.tables[A.sett['pressure']][0])
#    data2=A.sel_onlypulse(['time','Q','Tmc','index'],A.tables[A.sett['pressure']][1])
#    A.nopulse1,A.nopulse2=A.pulse_remove(15,35,data1,data2) # for 0 bar
#    A.nopulse1,A.nopulse2=A.pulse_remove(10,50,data1,data2) # for 9 psi and 22 bar
#    del data1
#    del data2
#    f_lt,f_tl=A.temp_fit(1)
#    f_lt,f_tl=A.temp_fit(3) # 9psi
#    f_lt,f_tl=A.temp_fit(4) # for 22 bar
#    fit_qt=A.QtoT(10) # optimal for 0 bar and 9 psi
#    fit_qt=A.QtoT(16) # for 22 bar
#    dQ=A.QtoTic(fit_qt)
#    A.update_local(A.tables[A.sett['pressure']][0],fit_qt,0)
#    A.update_local(A.tables[A.sett['pressure']][1],fit_qt,dQ)
    # setattr(A.pick_sep,"callme",True)
    # A.pick_sep.callme=True
    p_num = A.loop_number()
#    f_par=[A.pick_sep(ii,1000) for ii in range(p_num)]
#    A.plot_dt(f_par)
#    A.save_dt(f_par)
    dataJ = A.sel_onlypulseJoin(['time', 'Q', 'Tloc/Tc', 'index', 'pulse'], A.tables[A.sett['pressure']]
                                [0], ['Q', 'Tloc/Tc', 'Tmc/Tc'], A.tables[A.sett['pressure']][1])
    f1, f2, f3, fnum, Tmc = A.dlocal(dataJ, p_num, 10)
    slopes = A.dpart(f1, f2, f3, fnum, p_num-4, Tmc)
#    A.saveslopes(slopes,Tmc)
    A.close_f()
    del A
    # print(A.save_dt.__doc__)
    if toplot:

        fig1 = plt.figure(1, clear=True)
        ax1 = fig1.add_subplot(211)
        ax1.set_ylabel('Q')
        ax1.set_xlabel('time [sec]')
        ax1.set_title('Q vs time for both forks')
        ax1.scatter(dataJ[0], dataJ[1], color='green', s=0.5)
        ax1.scatter(dataJ[0], dataJ[5], color='red', s=0.5)
        plt.grid()
        ax2 = fig1.add_subplot(212)
        ax2.set_ylabel('T')
        ax2.set_xlabel('time [sec]')
        ax2.set_title('T vs time for both forks')
        ax2.scatter(dataJ[0], dataJ[2], color='green', s=0.5)
        ax2.scatter(dataJ[0], dataJ[6], color='red', s=0.5)
        plt.grid()
        # plt.show()
        fig2 = plt.figure(2, clear=True)
        ax1 = fig2.add_subplot(111)
        ax1.set_ylabel('pulse')
        ax1.set_xlabel('time [sec]')
        ax1.set_title('pulse vs time for both forks')
        ax1.scatter(dataJ[0], dataJ[4], color='green', s=0.5)
        plt.grid()
        # plt.show()
    plt.show()
