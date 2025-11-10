import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import joblib

# Step 1: Load Data
print("=" * 50)
print("📊 Salary Prediction with Linear Regression")
print("=" * 50)

df = pd.read_csv("Salary_dataset.csv")
print("\n📋 Data Preview:")
print(df.head())

# Step 2: Explore Data
print("\n📈 Data Shape:", df.shape)
print("\n📊 Statistics:")
print(df.describe())

# Step 3: Prepare Data
X = df[["YearsExperience"]]  # 2D - Features
y = df["Salary"]              # 1D - Target

print(f"\n✅ X shape: {X.shape} - 2D")
print(f"✅ y shape: {y.shape} - 1D")

# Step 4: Create and Train Model
model = LinearRegression()
model.fit(X, y)
print("\n🎓 Model trained!")

# Step 5: View Model Parameters
slope = model.coef_[0]
intercept = model.intercept_
print(f"\n📐 Linear Equation:")
print(f"   y = {slope:.2f}x + {intercept:.2f}")
print(f"   Salary = {slope:.2f} × YearsExperience + {intercept:.2f}")

# Step 6: Evaluate Model
r2 = model.score(X, y)
print(f"\n⭐ R² Score: {r2:.4f}")
print(f"   Model explains {r2*100:.2f}% of variance")

# Step 7: Make Predictions
print("\n🔮 Prediction Examples:")
test_years = [5.0, 10.0, 15.0]
for years in test_years:
    new_data = pd.DataFrame({"YearsExperience": [years]})
    prediction = model.predict(new_data)
    print(f"   {years} years experience → ${prediction[0]:,.2f}")

# Step 8: Visualization
plt.figure(figsize=(14, 5))

# Subplot 1: Linear Regression with predictions
plt.subplot(1, 2, 1)
plt.scatter(X, y, color='blue', alpha=0.7, s=80, label='Actual Data', edgecolors='black', linewidth=0.5)
plt.plot(X, model.predict(X), color='red', linewidth=2.5, label=f'Regression Line\ny = {slope:.2f}x + {intercept:.2f}')
# Add some prediction points
prediction_years = np.array([[3], [7], [10]])
prediction_salaries = model.predict(prediction_years)
plt.scatter(prediction_years, prediction_salaries, color='green', marker='*', s=300, 
            label='Predictions', edgecolors='black', linewidth=1, zorder=5)
plt.xlabel('Years of Experience', fontsize=11)
plt.ylabel('Salary (DKK)', fontsize=11)
plt.title('Linear Regression: Experience vs. Salary', fontsize=12, fontweight='bold')
plt.legend(loc='upper left')
plt.grid(True, alpha=0.3)

# Subplot 2: Data distribution (scatter plot only)
plt.subplot(1, 2, 2)
plt.scatter(X, y, color='blue', alpha=0.7, s=80, edgecolors='black', linewidth=0.5)
plt.xlabel('Years of Experience', fontsize=11)
plt.ylabel('Salary (DKK)', fontsize=11)
plt.title('Years of Experience vs. Salary', fontsize=12, fontweight='bold')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('salary_analysis.png', dpi=300, bbox_inches='tight')
print("\n📊 Chart saved: salary_analysis.png")
print("   (Close the plot window to continue...)")
plt.show()

# Step 9: Save Model
joblib.dump(model, "salary_model.joblib")
print("\n💾 Model saved: salary_model.joblib")

print("\n" + "=" * 50)
print("✅ Analysis Complete!")
print("=" * 50)

# Keep window open
input("\nPress Enter to exit...")
