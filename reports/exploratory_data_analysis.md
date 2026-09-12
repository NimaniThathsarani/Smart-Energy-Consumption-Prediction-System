### **EDA Findings**

* The dataset contains 2,075,259 records collected at one-minute intervals.
* The observation period ranges from December 2006 to November 2010.
* The data is chronologically ordered with no duplicate timestamps.
* Global\_active\_power was selected as the main energy-consumption variable.
* Electricity consumption varies across different hours of the day.
* Peak and low consumption hours were identified using hourly average power.
* Daily and weekly trends show recurring household consumption patterns.
* Monthly analysis reveals seasonal changes in energy demand.
* Weekday and weekend consumption patterns were compared to identify differences in household behaviour.
* The active-power distribution is concentrated at lower values, with occasional high-demand peaks.
* Extreme values were retained because they may represent genuine electricity usage rather than errors.
* Correlation analysis examined relationships among active power, reactive power, voltage, current intensity, and sub-metering values.
* Seasonal decomposition separated the consumption data into trend, seasonal, and residual components.
* The month-hour heatmap showed how consumption changes across different months and hours.
* The analysis confirms that time-based features such as hour, day, month, weekday/weekend status, and historical power values are useful for prediction.
* The dataset contains 25,903 missing measurement rows caused by long gaps, which must be handled during model preparation.
* Overall, the EDA shows that household electricity consumption has clear temporal and seasonal patterns suitable for forecasting.

