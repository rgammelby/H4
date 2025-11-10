import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

CSV_NAME = "Salary_dataset.csv"

# This function evaluates the model
def evaluate(model, X_tr, y_tr, X_te, y_te, name="Model"):
    """
    Evaluate model performance on training and test data
    """
    y_pred_tr = model.predict(X_tr)
    y_pred_te = model.predict(X_te)
    
    # Calculate metrics
    mse_tr = mean_squared_error(y_tr, y_pred_tr)
    mse_te = mean_squared_error(y_te, y_pred_te)
    rmse_tr = np.sqrt(mse_tr)
    rmse_te = np.sqrt(mse_te)
    mae_tr = mean_absolute_error(y_tr, y_pred_tr)
    mae_te = mean_absolute_error(y_te, y_pred_te)
    r2_tr = r2_score(y_tr, y_pred_tr)
    r2_te = r2_score(y_te, y_pred_te)
    
    print(f"\n=== {name} ===")
    print(f"Train -> MSE: {mse_tr:.2f}, RMSE: {rmse_tr:.2f}, MAE: {mae_tr:.2f}, R²: {r2_tr:.4f}")
    print(f"Test  -> MSE: {mse_te:.2f}, RMSE: {rmse_te:.2f}, MAE: {mae_te:.2f}, R²: {r2_te:.4f}")
    
    return {
        'mse_train': mse_tr, 'mse_test': mse_te,
        'rmse_train': rmse_tr, 'rmse_test': rmse_te,
        'mae_train': mae_tr, 'mae_test': mae_te,
        'r2_train': r2_tr, 'r2_test': r2_te
    }


def main():
    print("=" * 60)
    print("💰 Salary Prediction with Train/Test Split")
    print("=" * 60)
    
    # Load data
    df = pd.read_csv(CSV_NAME)
    print("\n📋 Data Preview:")
    print(df.head())
    print(f"\n📊 Total samples: {len(df)}")
    
    # Prepare features and target
    X = df[["YearsExperience"]]
    y = df["Salary"]
    
    # Split data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\n✂️ Data Split:")
    print(f"   Training set size: {len(X_train)} samples ({len(X_train)/len(df)*100:.0f}%)")
    print(f"   Test set size: {len(X_test)} samples ({len(X_test)/len(df)*100:.0f}%)")
    
    # Create and train model
    model = LinearRegression()
    model.fit(X_train, y_train)
    print("\n🎓 Model trained successfully!")
    
    # Model parameters
    slope = model.coef_[0]
    intercept = model.intercept_
    print(f"\n📐 Linear Equation:")
    print(f"   Salary = {slope:.2f} × YearsExperience + {intercept:.2f}")
    
    # Evaluate model
    metrics = evaluate(model, X_train, y_train, X_test, y_test, "Linear Regression")
    
    # Make predictions on test set
    print("\n🔮 Sample Predictions on Test Data:")
    y_pred_test = model.predict(X_test)
    test_results = pd.DataFrame({
        'Years': X_test['YearsExperience'].values,
        'Actual Salary': y_test.values,
        'Predicted Salary': y_pred_test,
        'Error': y_test.values - y_pred_test
    })
    test_results = test_results.sort_values('Years')
    print(test_results.head(6).to_string(index=False))
    
    # Visualization
    x_min = X["YearsExperience"].min()
    x_max = X["YearsExperience"].max()
    X_line = pd.DataFrame({"YearsExperience": np.linspace(x_min, x_max, 100)})
    y_line = model.predict(X_line)
    
    plt.figure(figsize=(14, 5))
    
    # Plot 1: Training and Test Data with Regression Line
    plt.subplot(1, 2, 1)
    plt.scatter(X_train, y_train, color='blue', alpha=0.6, label='Training Data', s=80)
    plt.scatter(X_test, y_test, color='green', alpha=0.6, label='Test Data', s=80)
    plt.plot(X_line, y_line, color='red', linewidth=2, label='Regression Line')
    plt.xlabel('Years of Experience')
    plt.ylabel('Salary ($)')
    plt.title('Salary Prediction: Train/Test Split')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Predictions vs Actual
    plt.subplot(1, 2, 2)
    plt.scatter(y_test, y_pred_test, color='purple', alpha=0.6, s=80)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 
             'r--', linewidth=2, label='Perfect Prediction')
    plt.xlabel('Actual Salary ($)')
    plt.ylabel('Predicted Salary ($)')
    plt.title('Predictions vs Actual (Test Set)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('salary_train_test.png', dpi=300, bbox_inches='tight')
    print("\n📊 Chart saved: salary_train_test.png")
    plt.show()
    
    # Additional predictions
    print("\n🔮 Predictions for New Data:")
    new_years = [3.0, 7.0, 12.0, 15.0]
    for years in new_years:
        new_data = pd.DataFrame({"YearsExperience": [years]})
        prediction = model.predict(new_data)
        print(f"   {years} years experience → ${prediction[0]:,.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Analysis Complete!")
    print("=" * 60)
    
    # Keep window open
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
