import pandas as pd

df = pd.read_csv(
    "birthday_names.csv"
)

for _, row in df.iterrows():

    name = row["name"]
    message = row["message"]

    # generate video

    # upload youtube

    print(
        f"Completed {name}"
    )
