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
1. The __createdata.py__, database was created using the original .dat files for three different pressures and two quartz forks./
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
  * _pulse_ are updated by 1000 per pulse
  * update _pulse_ with negative number in the vicinity where pulse is lunches, i.e. abs(`Q`) is large
  * non-linear regression fit of `T_mc` vs `time` dependence
  * update `Tmc/Tc` with the fitted values
  * non linear regression fit of the `Tmc/Tc` vs `Q` for _HEC_ table
  * update `Tloc` and `Tloc/Tc` for _HEC_
  * update `Tloc` and `Tloc/Tc` for _IC_
  * find _dT<sub>HEC</sub>_/_dT<sub>IC</sub>_
