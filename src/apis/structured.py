import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import platform

if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic')

plt.rc('axes', unicode_minus=False)

data = {
    "version": ["before"] * 10 + ["after"] * 10,
    "accuracy": [0.8, 0.82, 0.78, 0.79, 0.81, 0.83, 0.80, 0.82, 0.79, 0.81,
                 0.88, 0.87, 0.90, 0.89, 0.92, 0.91, 0.93, 0.89, 0.88, 0.90],
    "response_time": [0.45, 0.47, 0.46, 0.48, 0.44, 0.46, 0.45, 0.47, 0.46, 0.48,
                      0.35, 0.34, 0.36, 0.37, 0.34, 0.35, 0.36, 0.37, 0.35, 0.36]
}

df = pd.DataFrame(data)

plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
sns.boxplot(x="version", y="accuracy", data=df)
plt.title("정확도 비교")

plt.subplot(1, 2, 2)
sns.boxplot(x="version", y="response_time", data=df)
plt.title("응답 시간 비교")

plt.tight_layout()
plt.show()