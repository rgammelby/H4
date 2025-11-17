import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, learning_curve
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, mean_squared_error, r2_score

# Load dataset
data = sns.load_dataset("diamonds")
#print(data.columns)
#data.head()
#data.info()
#data.describe()
#data.isna().sum()

# Clean up faulty or lacking data points
data = data.dropna()

# Create a price level column for classification
data["price_level"] = pd.qcut(data["price"], 3, labels=["low", "medium", "high"])

# Identify categorical and numeric columns
categorical_cols = ["cut", "color", "clarity"]
numeric_cols = ["carat", "depth", "table", "x", "y", "z"]

# Encode categorical columns into numeric dummy variables
encoded_cats = pd.get_dummies(data[categorical_cols], drop_first=True)

# Classification data 
X_class = pd.concat([data[numeric_cols], encoded_cats], axis=1)
y_class = data["price_level"]

# Regression data 
X_reg = pd.concat([data[numeric_cols], encoded_cats], axis=1)
y_reg = data["price"]



# Split into training and testing sets 
Xc_train, Xc_test, yc_train, yc_test = train_test_split(X_class, y_class, test_size=0.2, random_state=42)
Xr_train, Xr_test, yr_train, yr_test = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)

# Classification: Decision Tree
tree_model_c = DecisionTreeClassifier(max_depth=1, random_state=42)
tree_model_c.fit(Xc_train, yc_train)

y_pred_tree_c = tree_model_c.predict(Xc_test)
print("\n--- Decision Tree (Classification) ---")
print("Accuracy:", accuracy_score(yc_test, y_pred_tree_c))
#print("Confusion Matrix:\n", confusion_matrix(yc_test, y_pred_tree_c))
#print("Classification Report:\n", classification_report(yc_test, y_pred_tree_c))

# Classification: KNN 
knn_model_c = KNeighborsClassifier(n_neighbors=1)
knn_model_c.fit(Xc_train, yc_train)

y_pred_knn_c = knn_model_c.predict(Xc_test)
print("\n--- KNN (Classification) ---")
print("Accuracy:", accuracy_score(yc_test, y_pred_knn_c))
#print("Confusion Matrix:\n", confusion_matrix(yc_test, y_pred_knn_c))
#print("Classification Report:\n", classification_report(yc_test, y_pred_knn_c))

# Replace uses of mean_squared_error(..., squared=False) with explicit sqrt for compatibility

# Regression: Decision Tree
tree_model_r = DecisionTreeRegressor(max_depth=1, random_state=42)
tree_model_r.fit(Xr_train, yr_train)
y_pred_tree_r = tree_model_r.predict(Xr_test)

# Regression: KNN 
knn_model_r = KNeighborsRegressor(n_neighbors=1)
knn_model_r.fit(Xr_train, yr_train)
y_pred_knn_r = knn_model_r.predict(Xr_test)

# Regression: Decision Tree (print RMSE)
rmse_tree = mean_squared_error(yr_test, y_pred_tree_r)  # MSE
print("\n--- Decision Tree (Regression) ---")
print("RMSE:", np.sqrt(rmse_tree))
print("R²:", r2_score(yr_test, y_pred_tree_r))

# Regression: KNN (print RMSE) 
rmse_knn = mean_squared_error(yr_test, y_pred_knn_r)  # MSE
print("\n--- KNN (Regression) ---")
print("RMSE:", np.sqrt(rmse_knn))
print("R²:", r2_score(yr_test, y_pred_knn_r))

#print("Accuracy for max_depth 5 (Decision Tree): \n0.9228772710418984")
#print("Accuracy for n_neighbors 5 (KNN): \n0.9167593622543567")