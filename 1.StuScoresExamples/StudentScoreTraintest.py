import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score

CSV_NAME = "student_scores.csv"

# Denne funktion evaluere modellen
def evaluate(model, X_tr, y_tr, X_te, y_te, name="Model"):
    y_pred_tr = model.predict(X_tr)
    y_pred_te = model.predict(X_te)
    mse_tr = mean_squared_error(y_tr, y_pred_tr)
    mse_te = mean_squared_error(y_te, y_pred_te)
    r2_tr = r2_score(y_tr, y_pred_tr)
    r2_te = r2_score(y_te, y_pred_te)
    print(f"\n=== {name} ===")
    print(f"Train -> MSE: {mse_tr:.3f}, R^2: {r2_tr:.3f}")
    print(f"Test -> MSE: {mse_te:.3f}, R^2: {r2_te:.3f}")




def main():
    df = pd.read_csv(CSV_NAME)

    print(df.head())

    X = df[["Hours"]]
    y = df["Scores"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=3)
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    linear = LinearRegression()
    linear.fit(X_train, y_train)

    evaluate(linear, X_train, y_train, X_test, y_test, "Linear Regression")

    #Visualier
    x_min = X["Hours"].min()
    x_max = X["Hours"].max()

    X_line = pd.DataFrame({"Hours": np.linspace(x_min, x_max, 100)})
    y_line = linear.predict(X_line)

    plt.figure()
    plt.scatter(X_train, y_train, label="Training data")
    plt.scatter(X_test, y_test, label="Test data")
    plt.plot(X_line, y_line, label="Linear Regression")
    plt.xlabel("Hours")
    plt.ylabel("Score")
    plt.title("Train/Test")
    plt.legend()
    plt.tight_layout()
    plt.show()

    """"
    #Overfitting demo
    poly_degree = 0
    poly_model = Pipeline([
        ("poly", PolynomialFeatures(degree=poly_degree, include_bias=True)),
        ("linreg", LinearRegression())
    ])
    poly_model.fit(X_train, y_train)
    poly_metrics = evaluate(poly_model, X_train, y_train, X_test, y_test, f"Polynomiel regression (grad={poly_degree})")

    # Plot for polynomiel model
    y_line_poly = poly_model.predict(X_line)
    plt.figure()
    plt.scatter(X_train, y_train, label="Train")
    plt.scatter(X_test, y_test, label="Test")
    plt.plot(X_line, y_line_poly, label=f"Poly grad={poly_degree}")
    plt.xlabel("Hours studied")
    plt.ylabel("Score")
    plt.title("Overfitting-demo: Polynomiel model")
    plt.legend()
    plt.tight_layout()
    plt.show()
    """


if __name__ == "__main__":
    main()