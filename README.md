# pulses_sql
Pulses analysis using MySQL server for data saving.\
The code is focused on the comprehensive analysis of the data measured on a liquid <sup>3</sup>He in Cornell University.

![alt text](https://github.com/dlotnyk/pulses_sql/blob/master/cornell_logo.png "Cornell University")

## Version

The code was developed in the __Anaconda__ environment 5.3.0,  
__Python__ build: 3.7.0

## Dependencies
numpy\
matplotlib\
scipy\
mysql.connector\
inspect

## Description

The code consists of two parts.
1. The __createdata.py__, database was created using the original .dat files for three different pressures and two quartz forks.\
Additionally, three wrapper functions for _decorators_ were created in order to log called method, estimate processing time, and call tracking. Even all columns were updated only several will not change and those are the _raw_ :  
`index`, `time`, `Q`, `Inf_Freq`, `Tmc`
`pulse` columns are the primary and foreign keys and can be cascadely updated. The as follows
  * Connect to SQL database using `conf` dict;
  * Delete any tables if any;
  * Create all necessary tables;
  * Close connection.
2. The __tauanalysis.py__ uses and updates an existing database. Here separate pulses are identified according to `Q` in _IC_ tables. The `pulse` updates from the number greater than the number of elements in column by 1000 per each pulse. The logic is the next:
  * import data with `Q`'s
  * Find indices where abs(`Q`) is really high
  * `pulse` are updated by 1000 per pulse
  * update `pulse` with negative number in the vicinity where pulse is lunches, i.e. abs(`Q`) is large
  * non-linear regression fit of `T_mc` vs `time` dependence
  * update `Tmc/Tc` with the fitted values
  * non linear regression fit of the `Tmc/Tc` vs `Q` for _HEC_ table
  * update `Tloc` and `Tloc/Tc` for _HEC_
  * update `Tloc` and `Tloc/Tc` for _IC_
  * find _dT<sub>HEC</sub>_/_dT<sub>IC</sub>_
## Usage
### createdata.py
The sequence of commands as follows:
```
A=sql_create(conf)
A.filt_num=41
A.drop_f(forks)
for k,v in forks.items():
    A.create_table(v['tables'][0],v['tables'][1])
    A.insert_tables(v)
A.close_f()  
```
It will create tables and inserts raw data for further analysis.
It is recommended to comment all these commands (with #) after one execution.
### tauanalysis.py
#### First execution:
```
A=timetotemp(conf,sett1)
A.first_start()
data1=A.sel_onlypulse(['time','Q','Tmc','index','pulse'],A.tables[A.sett['pressure']][0])
data2=A.sel_onlypulse(['time','Q','Tmc','index'],A.tables[A.sett['pressure']][1])
A.nopulse1,A.nopulse2=A.pulse_remove(15,35,data1,data2) # for 0 bar
A.nopulse1,A.nopulse2=A.pulse_remove(10,50,data1,data2) # for 9 psi and 22 bar
del data1
del data2
f_lt,f_tl=A.temp_fit(1)
f_lt,f_tl=A.temp_fit(3) # 9psi
f_lt,f_tl=A.temp_fit(4) # for 22 bar
fit_qt=A.QtoT(10) # optimal for 0 bar and 9 psi
fit_qt=A.QtoT(16) # for 22 bar
dQ=A.QtoTic(fit_qt)
A.update_local(A.tables[A.sett['pressure']][0],fit_qt,0)
A.update_local(A.tables[A.sett['pressure']][1],fit_qt,dQ)
del A
```
Change to `A=timetotemp(conf,sett2)` and `A=timetotemp(conf,sett3)` for different pressures and comment corresponding lines.
#### Further executions
```
A=timetotemp(conf,sett1)
p_num=A.loop_number()
f_par=[A.pick_sep(ii,100) for ii in range(p_num)]
A.plot_dt(f_par)
A.save_dt(f_par)
dataJ=A.sel_onlypulseJoin(['time','Q','Tloc/Tc','index','pulse'],A.tables[A.sett['pressure']][0],['Q','Tloc/Tc'],A.tables[A.sett['pressure']][1])
#print(A.save_dt.__doc__)
fig1 = plt.figure(1, clear = True)
ax1 = fig1.add_subplot(211)
ax1.set_ylabel('Q')
ax1.set_xlabel('time [sec]')
ax1.set_title('Q vs time for both forks')
ax1.scatter(dataJ[0],dataJ[1],color='green', s=0.5)
ax1.scatter(dataJ[0],dataJ[5],color='red', s=0.5)
plt.grid()
ax2 = fig1.add_subplot(212)
ax2.set_ylabel('T')
ax2.set_xlabel('time [sec]')
ax2.set_title('T vs time for both forks')
ax2.scatter(dataJ[0],dataJ[2],color='green', s=0.5)
ax2.scatter(dataJ[0],dataJ[6],color='red', s=0.5)
plt.grid()
plt.show()

fig2 = plt.figure(2, clear = True)
ax1 = fig2.add_subplot(111)
ax1.set_ylabel('pulse')
ax1.set_xlabel('time [sec]')
ax1.set_title('pulse vs time for both forks')
ax1.scatter(dataJ[0],dataJ[4],color='green', s=0.5)
plt.grid()
plt.show()
A.close_f()
del A
```
It will calculates and save the desired values of _dT<sub>HEC</sub>_/_dT<sub>IC</sub>_
Replace to `A=timetotemp(conf,sett2)` or `A=timetotemp(conf,sett3)` for different pressures.
## Testing
### test_createdata.py
Just excecute this file for a unit test of the __createdata.py__.
### test_tauanalysis.py
In progress...
## Licence 
Cornell University &copy; Dmytro Lotnyk
