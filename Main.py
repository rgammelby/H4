import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import joblib

CSV_PATH = "student_scores.csv"  # skal have kolonnerne: Hours, Scores

def main():
    #"Indlæs og kig på data
    df = pd.read_csv(CSV_PATH)
    print(df.head())

    #Scatter-plot over Hours vs. Scores
    plt.figure()
    plt.scatter(df["Hours"], df["Scores"], alpha=0.85)
    plt.title("Study Hours vs. Exam Score")
    plt.xlabel("Hours")
    plt.ylabel("Score")
    plt.tight_layout()
    #plt.show()

    #Forbered X (2D) og y (1D)
    X = df[["Hours"]]          # 2D (n,1) 2D fordi vi skal have n, som er antal data eksmepler og featuren "Hour" med
    y = df["Scores"]           # 1D (n) 1D Her skal vi bare have vores target score n, som skal gættes af modellen.

    #Træn en simpel lineær regression
    model = LinearRegression().fit(X, y)

    intercept = float(model.intercept_)      # forventet score ved 0 timer (b)
    slope = float(model.coef_[0])           # point pr. time (a)
    print(f"Model: ŷ = {slope:.3f} * Hours + {intercept:.3f}")
    print(f"Fortolkning: For hver ekstra time: +{slope:.2f} point i snit.")
    print(f"Intercept (0 timer): {intercept:.2f} point")

    #En forudsigelse for et konkret antal timer (eksempel)
    hours = 4
    pred = float(model.predict(pd.DataFrame({'Hours':[hours]}))[0])
    print(f"Forventet score for {hours} timers læsning: {pred:.2f}")

    #Tegn regressionslinjen glat hen over dataområdet
    x_min, x_max = df["Hours"].min(), df["Hours"].max()
    X_line = pd.DataFrame({"Hours": np.linspace(x_min, x_max, 200)}) #For deler 200 punkter jævnt mellem x_min og x_max
    y_line = model.predict(X_line)

    plt.figure()
    plt.scatter(df["Hours"], df["Scores"], alpha=0.85, label="Data")
    plt.plot(X_line["Hours"], y_line, label="Linear Regression")
    plt.title("Linear Regression Fit")
    plt.xlabel("Hours")
    plt.ylabel("Score")
    plt.legend()
    plt.tight_layout()
    plt.show()

    joblib.dump(model, 'student_score_model.joblib')
    print("Model gemt")

if __name__ == "__main__":
    main()
