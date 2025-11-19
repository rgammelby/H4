import os
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, mean_squared_error, r2_score

# Load dataset
data = sns.load_dataset("diamonds")

# Descriptions of dataset (debug)
#print(data.columns)
#data.head()
#data.info()
#data.describe()
#print(f"Faulty/lacking data points per column: \n{data.isna().sum()}")

# Print dataset (debug)
'''
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, "diamonds.csv")
data.to_csv(output_path, index=False)
'''

# Clean up faulty or lacking data points just to be safe
data = data.dropna()

# Create a price level column for classification
data["price_level"] = pd.qcut(data["price"], 3, labels=["low", "medium", "high"])

# Identify categorical and numeric columns
categorical_cols = ["cut", "color", "clarity"]
numeric_cols = ["carat", "depth", "table", "x", "y", "z"]

print(f"Price level value counts: \n{data["price_level"].value_counts()}")
#print(f"Numeric columns description: \n{data[numeric_cols].describe()}")

# Encode categorical columns into numeric dummy variables
encoded_cats = pd.get_dummies(data[categorical_cols], drop_first=True)

# Classification data 
X_class = pd.concat([data[numeric_cols], encoded_cats], axis=1)
y_class = data["price_level"]

# Regression data 
X_reg = pd.concat([data[numeric_cols], encoded_cats], axis=1)
y_reg = data["price"]

#  Cross-validation for the Classification Tree 
clf_for_cv = DecisionTreeClassifier(max_depth=15, random_state=42)
cv_scores_class = cross_val_score(clf_for_cv, X_class, y_class, cv=5, scoring="accuracy")
print("\n Cross-validation (Classification) ")
print("Accuracy scores:", cv_scores_class)
print("Mean accuracy:", cv_scores_class.mean())

# Split into training and testing sets 
# Classification, stratified to ensure an equal distribution of data in both sets
Xc_train, Xc_test, yc_train, yc_test = train_test_split(
    X_class, y_class,
    test_size=0.2,
    random_state=42,
    stratify=y_class
)

# Regression data split
Xr_train, Xr_test, yr_train, yr_test = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)

# Classification model: Decision Tree
tree_model_c = DecisionTreeClassifier(max_depth=15, random_state=42)
tree_model_c.fit(Xc_train, yc_train)

# Predict (classification)
y_pred_tree_c = tree_model_c.predict(Xc_test)
print("\n Decision Tree (Classification) ")
print("Accuracy:", accuracy_score(yc_test, y_pred_tree_c))

# Print confusion matrix and classification report
print("Confusion Matrix:\n", confusion_matrix(yc_test, y_pred_tree_c))
print("Classification Report:\n", classification_report(yc_test, y_pred_tree_c))

# Classification Feature Importances (sorted)
importances_c = sorted(zip(X_class.columns, tree_model_c.feature_importances_), key=lambda x: x[1], reverse=True)

# Regression model: Decision Tree
tree_model_r = DecisionTreeRegressor(max_depth=15, random_state=42)
tree_model_r.fit(Xr_train, yr_train)

# Predict (regression)
y_pred_tree_r = tree_model_r.predict(Xr_test)

# Regression: Decision Tree (print RMSE)
rmse_tree = mean_squared_error(yr_test, y_pred_tree_r)  # MSE
print("\n Decision Tree (Regression) ")
print("RMSE:", np.sqrt(rmse_tree))
print("R²:", r2_score(yr_test, y_pred_tree_r))

# Regression Feature Importances (sorted)
importances_r = sorted(zip(X_reg.columns, tree_model_r.feature_importances_), key=lambda x: x[1], reverse=True)

# Create graphs folder if missing
script_dir = os.path.dirname(os.path.abspath(__file__))
graphs_dir = os.path.join(script_dir, "graphs")
os.makedirs(graphs_dir, exist_ok=True)

# Feature Importances – Classification
plt.figure(figsize=(10, 6))
names_c = [name for name, _ in importances_c]
vals_c = [val for _, val in importances_c]
plt.barh(names_c, vals_c)
plt.title("Feature Importances – Classification Tree")
plt.xlabel("Importance")
plt.ylabel("Feature")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(graphs_dir, "feature_importances_classification.png"))

# Feature Importances – Regression
plt.figure(figsize=(10, 6))
names_r = [name for name, _ in importances_r]
vals_r = [val for _, val in importances_r]
plt.barh(names_r, vals_r)
plt.title("Feature Importances – Regression Tree")
plt.xlabel("Importance")
plt.ylabel("Feature")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(graphs_dir, "feature_importances_regression.png"))

# Actual vs Predicted Prices (Regression)
plt.figure(figsize=(8, 6))
plt.scatter(yr_test, y_pred_tree_r, alpha=0.4)
plt.title("Actual vs Predicted Prices – Regression Tree")
plt.xlabel("Actual Price")
plt.ylabel("Predicted Price")
plt.tight_layout()
plt.savefig(os.path.join(graphs_dir, "actual_vs_predicted_prices.png"))

# Learning Curve – Classification
train_sizes, train_scores, val_scores = learning_curve(
    tree_model_c, X_class, y_class,
    train_sizes=np.linspace(0.1, 1.0, 10),
    cv=5,
    scoring='accuracy'
)

plt.figure(figsize=(8, 6))
plt.plot(train_sizes, train_scores.mean(axis=1), label="Training Score")
plt.plot(train_sizes, val_scores.mean(axis=1), label="Validation Score")
plt.title("Learning Curve – Classification Tree")
plt.xlabel("Training Set Size")
plt.ylabel("Accuracy")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(graphs_dir, "learning_curve_classification.png"))

# Learning Curve – Regression
train_sizes_r, train_scores_r, val_scores_r = learning_curve(
    tree_model_r, X_reg, y_reg,
    train_sizes=np.linspace(0.1, 1.0, 10),
    cv=5,
    scoring='r2'
)

plt.figure(figsize=(8, 6))
plt.plot(train_sizes_r, train_scores_r.mean(axis=1), label="Training R²")
plt.plot(train_sizes_r, val_scores_r.mean(axis=1), label="Validation R²")
plt.title("Learning Curve – Regression Tree")
plt.xlabel("Training Set Size")
plt.ylabel("R² Score")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(graphs_dir, "learning_curve_regression.png"))

# Distribution of Price
plt.figure(figsize=(8, 6))
plt.hist(data["price"], bins=50, alpha=0.7)
plt.title("Distribution of Price")
plt.xlabel("Price")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig(os.path.join(graphs_dir, "price_distribution.png"))

# Distribution of Carat
plt.figure(figsize=(8, 6))
plt.hist(data["carat"], bins=50, alpha=0.7)
plt.title("Distribution of Carat")
plt.xlabel("Carat")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig(os.path.join(graphs_dir, "carat_distribution.png"))

# Correlation Heatmap
plt.figure(figsize=(10, 8))
corr = data[numeric_cols + ["price"]].corr()
sns.heatmap(corr, annot=True, cmap="coolwarm")
plt.title("Correlation Heatmap – Numeric Features")
plt.tight_layout()
plt.savefig(os.path.join(graphs_dir, "correlation_heatmap.png"))

# Display graphs
plt.show()