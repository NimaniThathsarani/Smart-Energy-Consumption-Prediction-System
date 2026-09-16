# Member 3 – Validation and Model Comparison Report

## Smart Energy Consumption Prediction System

### 1. Introduction

The purpose of this work was to validate and compare the machine learning models developed for the Smart Energy Consumption Prediction System. The main responsibility of Member 3 was to evaluate the available forecasting models using consistent performance metrics, analyse prediction errors, compare model performance, select the best-performing model, and generate the final predictions.

Three machine learning models were evaluated:

* Random Forest Regressor
* Gradient Boosting Regressor
* XGBoost Regressor

The evaluation focused on predicting `Global_active_power`, which represents household energy consumption.

---

## 2. Dataset and Evaluation Setup

The feature-engineered dataset contained 2,047,446 observations. The dataset covered the period from 16 December 2006 to 26 November 2010.

The data was evaluated using a chronological train/validation/test structure to ensure that future observations were not used before earlier observations.

The planned split was:

| Dataset    | Number of Rows |
| ---------- | -------------: |
| Training   |      1,433,212 |
| Validation |        307,116 |
| Test       |        307,118 |

The chronological boundaries were:

* Training data ended at 13 September 2009 14:57.
* Validation data ended at 18 April 2010 17:05.
* Test data started at 18 April 2010 17:06.

After removing rows containing unavailable feature values, 307,117 observations were used for the final test evaluation.

The final test period evaluated the pretrained Member 1 machine learning models on a chronological held-out period. This allowed the models to be compared using the same test observations.

---

## 3. Input Features

The machine learning models used 17 features:

1. Global_reactive_power
2. Voltage
3. Global_intensity
4. Sub_metering_1
5. Sub_metering_2
6. Sub_metering_3
7. Hour
8. Day
9. Month
10. Weekend
11. Lag_1
12. Lag_24
13. Lag_168
14. RollingMean_24
15. RollingStd_24
16. Difference
17. PctChange

These features include electrical measurements, calendar information, lag features, rolling statistics, and change-based features.

Lag and rolling features were particularly useful for representing previous consumption behaviour and short-term patterns in the time-series data.

---

## 4. Evaluation Metrics

Four evaluation metrics were used to compare the models.

### 4.1 Mean Absolute Error (MAE)

MAE measures the average absolute difference between the actual and predicted values.

A lower MAE indicates that the model's predictions are closer to the actual energy consumption values.

### 4.2 Root Mean Squared Error (RMSE)

RMSE measures the square root of the average squared prediction error.

RMSE gives greater importance to larger errors. Therefore, a lower RMSE indicates better prediction accuracy and fewer large prediction errors.

### 4.3 Mean Absolute Percentage Error (MAPE)

MAPE measures prediction error as a percentage of the actual value.

A lower MAPE indicates better prediction accuracy. Because energy consumption can contain values close to zero, percentage-based errors should be interpreted carefully.

### 4.4 R² Score

R² measures how well the model explains the variation in the target variable.

An R² value closer to 1 indicates stronger predictive performance.

---

## 5. Model Evaluation Results

The three machine learning models were evaluated on the same chronological test dataset.

| Model             |         MAE |        RMSE |      MAPE |          R² |
| ----------------- | ----------: | ----------: | --------: | ----------: |
| Random Forest     |     0.02127 |     0.03777 |     3.06% |     0.99808 |
| Gradient Boosting |     0.15705 |     0.21137 |    37.66% |     0.93981 |
| XGBoost           | **0.01571** | **0.02845** | **2.36%** | **0.99891** |

The results show that XGBoost achieved the best performance across all four evaluation metrics.

---

## 6. Random Forest Evaluation

The Random Forest Regressor achieved the following results:

* MAE: 0.02127
* RMSE: 0.03777
* MAPE: 3.06%
* R²: 0.99808

The model produced highly accurate predictions, with an R² score very close to 1.

The relatively low MAE and RMSE indicate that the predictions were generally close to the actual energy consumption values.

Random Forest therefore performed well and provided a strong benchmark for comparison with the other machine learning models.

---

## 7. Gradient Boosting Evaluation

The Gradient Boosting Regressor achieved:

* MAE: 0.15705
* RMSE: 0.21137
* MAPE: 37.66%
* R²: 0.93981

Compared with Random Forest and XGBoost, Gradient Boosting produced significantly larger prediction errors.

Although its R² score of 0.93981 shows that the model still explained a large amount of the variation in energy consumption, its MAE, RMSE, and MAPE were considerably higher.

Therefore, Gradient Boosting was not selected as the final model.

---

## 8. XGBoost Evaluation

The XGBoost Regressor achieved the strongest overall performance:

* MAE: **0.01571**
* RMSE: **0.02845**
* MAPE: **2.36%**
* R²: **0.99891**

XGBoost had the lowest MAE, meaning it produced the smallest average absolute prediction error.

It also achieved the lowest RMSE, indicating that it handled larger prediction errors better than the other evaluated models.

Its MAPE of 2.36% was also the lowest among the three models.

Finally, XGBoost achieved the highest R² score of 0.99891.

Based on these results, XGBoost was selected as the best-performing model.

---

## 9. Model Comparison

The model comparison shows a clear performance difference.

Random Forest performed very well, with an R² score of 0.99808 and a low MAE of 0.02127.

Gradient Boosting performed less effectively, with considerably higher errors.

XGBoost provided the best overall results. It improved on Random Forest in every reported metric.

Compared with Random Forest:

* MAE decreased from 0.02127 to 0.01571.
* RMSE decreased from 0.03777 to 0.02845.
* MAPE decreased from 3.06% to 2.36%.
* R² increased from 0.99808 to 0.99891.

Therefore, XGBoost was selected as the final model for energy consumption prediction.

---

## 10. Actual vs Predicted Analysis

An Actual vs Predicted graph was generated for the XGBoost test predictions.

The graph compares the actual `Global_active_power` values with the values predicted by XGBoost over the test period.

The predicted values generally follow the movement of the actual energy consumption values. This visual comparison supports the numerical evaluation results, which showed a very low MAE and RMSE and a very high R² score.

The graph was saved as:

`reports/figures/xgboost_actual_vs_predicted.png`

---

## 11. Residual/Error Analysis

Residual analysis was performed using:

**Residual = Actual − Predicted**

The residual analysis graph was generated by plotting the actual values against the prediction residuals.

The purpose of this analysis was to identify whether the prediction errors showed obvious patterns or large deviations.

The graph was saved as:

`reports/figures/xgboost_residual_analysis.png`

The residual analysis provides an additional method of checking the quality of the XGBoost predictions beyond the numerical evaluation metrics.

---

## 12. Final Prediction Generation

After XGBoost was selected as the best-performing model, its predictions for the test dataset were saved for further use by the project.

The final prediction file is:

`reports/xgboost_test_predictions.csv`

The file contains:

* `Datetime`
* `Actual`
* `Predicted`
* `Residual`

A total of 307,117 test predictions were generated.

Example structure:

| Datetime            | Actual | Predicted | Residual |
| ------------------- | -----: | --------: | -------: |
| 2010-04-18 17:07:00 |  0.342 |  0.340738 | 0.001262 |
| 2010-04-18 17:08:00 |  0.340 |  0.337095 | 0.002905 |
| 2010-04-18 17:09:00 |  0.340 |  0.337728 | 0.002272 |
| 2010-04-18 17:10:00 |  0.252 |  0.244834 | 0.007166 |
| 2010-04-18 17:11:00 |  0.248 |  0.242174 | 0.005826 |

---

## 13. Saved Model Files

The evaluated machine learning models were preserved in the project repository:

* `models/random_forest.pkl`
* `models/gradient_boosting.pkl`
* `models/xgboost.pkl`

The XGBoost model was selected as the final model based on the evaluation results.

---

## 14. Project Deliverables

The following files were produced as part of the validation and model comparison work:

### Model files

`models/random_forest.pkl`

`models/gradient_boosting.pkl`

`models/xgboost.pkl`

### Evaluation results

`reports/member3_model_comparison.csv`

### Final predictions

`reports/xgboost_test_predictions.csv`

### Visualisations

`reports/figures/xgboost_actual_vs_predicted.png`

`reports/figures/xgboost_residual_analysis.png`

---

## 15. Best Model Selection

Based on the evaluation results, XGBoost was selected as the best model.

The main reasons for selecting XGBoost were:

1. It achieved the lowest MAE.
2. It achieved the lowest RMSE.
3. It achieved the lowest MAPE.
4. It achieved the highest R² score.
5. Its predictions closely followed the actual energy consumption values.

Therefore, XGBoost provides the strongest performance among the three evaluated machine learning models for this stage of the Smart Energy Consumption Prediction System.

---

## 16. Limitations and Considerations

The evaluation was performed using pretrained models from the previous development work and a newly defined chronological held-out test period. Therefore, the evaluation should be understood as a comparison of the existing trained models on the same test period rather than a complete retraining experiment using exactly the documented 70/15/15 split.

MAPE should also be interpreted carefully because energy consumption values can sometimes be close to zero. Percentage-based errors can become relatively large when the actual value is very small.

Despite these considerations, the consistent comparison across the same test observations provides useful evidence for selecting the strongest model among Random Forest, Gradient Boosting, and XGBoost.

---

## 17. Conclusion

The validation and model comparison stage successfully evaluated three machine learning models for the Smart Energy Consumption Prediction System.

Random Forest demonstrated strong performance, while Gradient Boosting produced comparatively higher prediction errors. XGBoost achieved the best results across all four evaluation metrics.

The final XGBoost results were:

* **MAE: 0.01571**
* **RMSE: 0.02845**
* **MAPE: 2.36%**
* **R²: 0.99891**

Based on these results, XGBoost was selected as the best-performing model.

The final test predictions, residual values, model comparison results, trained model files, and visualisations were saved in the project repository. These outputs provide the basis for using the selected model in the later stages of the Smart Energy Consumption Prediction System.
