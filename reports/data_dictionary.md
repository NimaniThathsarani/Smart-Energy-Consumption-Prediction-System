# Data Dictionary

## Final Dataset

The final file is `data/processed/energy_clean.csv`. It contains one row per observed household electricity timestamp. The dataset is ordered chronologically and uses a one-minute cadence.

| Column | Type | Unit | Description |
|---|---|---|---|
| `Date` | string | `DD/MM/YYYY` | Original calendar date retained for traceability. |
| `Time` | string | `HH:MM:SS` | Original clock time retained for traceability. |
| `Timestamp` | `datetime64[ns]` in memory | minute timestamp | Combined, validated date-time used for sorting and time-series indexing. |
| `Global_active_power` | float64 | kilowatts (kW) | Primary prediction target; household global active power. |
| `Global_reactive_power` | float64 | kilowatts (kW) | Household global reactive power. |
| `Voltage` | float64 | volts (V) | Minute-averaged household voltage. |
| `Global_intensity` | float64 | amperes (A) | Minute-averaged household current intensity. |
| `Sub_metering_1` | float64 | watt-hours (Wh) | Energy sub-metering for kitchen appliances. |
| `Sub_metering_2` | float64 | watt-hours (Wh) | Energy sub-metering for laundry appliances. |
| `Sub_metering_3` | float64 | watt-hours (Wh) | Energy sub-metering for climate-control and water-heating appliances. |

## Missing-Data Policy

Member 1 interpolated complete gaps of five minutes or less. The remaining 25,903 rows with missing measurement values are long gaps and remain missing in the final dataset. Timestamp rows are preserved, and no long gap is silently interpolated or dropped. Each downstream model must explicitly choose a compatible policy, such as selecting complete target windows or applying a model-specific imputation method.

Zero measurements and genuine extreme peaks are retained. Statistical IQR outlier flags are screening information, not automatic deletion rules.
