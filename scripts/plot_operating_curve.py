import pandas as pd
import matplotlib.pyplot as plt

data = [
    (1.0, 0.706, 878669),
    (1.1, 0.706, 879399),
    (1.2, 0.750, 762123),
    (1.3, 0.882, 609142),
    (1.4, 0.941, 586452),
    (1.5, 0.941, 586452),
]

df = pd.DataFrame(data, columns=["multiplier", "recall", "cost"])

# Recall plot
plt.figure()
plt.plot(df["multiplier"], df["recall"], marker='o')
plt.xlabel("Alert Budget Multiplier")
plt.ylabel("Recall")
plt.title("Recall vs Alert Capacity")
plt.grid()
plt.show()

# Cost plot
plt.figure()
plt.plot(df["multiplier"], df["cost"], marker='o')
plt.xlabel("Alert Budget Multiplier")
plt.ylabel("Total Cost")
plt.title("Cost vs Alert Capacity")
plt.grid()
plt.show()