import re
from pathlib import Path

import pandas as pd
import shutil


OUT_PATH = Path("out/")


def format_entries(cards: pd.DataFrame, deck: pd.DataFrame, deck_info: bool = True) -> pd.Series:
    cards = cards.copy()

    cards["quantity"] = cards["quantity"].astype(str)
    cards["set_id"] = cards["set_id"].map(lambda set_id: f"[{set_id}]" if set_id else None)
    cards["variation"] = cards["variation"].map(
        lambda variation: f"<{variation}>" if variation else None
    )
    cards["foil"] = cards["foil"].map(lambda foil: "(F)" if foil == "foil" else None)
    cards["quantity"] = cards.apply(
        lambda entry: deck.loc[deck["card"] == entry["card"]].iloc[0]["quantity"],
        axis=1,
    )
    print(cards)

    columns = ["quantity", "card", "variation", "set_id", "foil"]
    return cards.apply(
        lambda entry: " | ".join(
            filter(
                None,
                [
                    f'{entry["deck"]:<{cards["deck"].str.len().max()}}' if deck_info else None,
                    " ".join(entry[col] for col in columns if entry[col]),
                ],
            )
        ),
        axis=1,
    )


def main(
    collection_path: str = "data/my_collection.csv",
    cards_dir: str = "data/cards/",
    decks_dir: str = "data/decks/",
) -> None:
    KEEP_COLS = ["Card", "Variation", "Set ID", "Foil", "Quantity"]
    RENAME_DICT = {col: col.lower().replace(" ", "_") for col in KEEP_COLS}
    NEW_COLS = list(RENAME_DICT.values())

    collection = pd.read_csv(collection_path)[KEEP_COLS].rename(columns=RENAME_DICT)
    collection["card"] = collection["card"].str.replace(" // ", "/")

    pattern = re.compile(
        r"(?P<quantity>\d+) (?P<card>[^[<]+\b)"
        r"( <(?P<variation>.+)>)?"
        r"( \[(?P<set_id>\w+)\])?"
        r"( (?P<foil>\(F\)))?"
    )

    available_cards = []
    for path in sorted(Path(cards_dir).rglob("*.txt")):
        print(path)
        if path.stem.startswith("Deck - "):
            path = path.rename(path.with_stem(path.stem.removeprefix("Deck - ")))

        with path.open("r") as fp:
            lines = fp.read().splitlines()

        cards = pd.DataFrame([pattern.match(line).groupdict() for line in lines if len(line)])
        cards["foil"] = cards["foil"].map(lambda x: "foil" if x else "regular")

        cards["deck"] = path.stem
        available_cards.append(cards)

    deck_list = []
    for path in sorted(Path(decks_dir).rglob("*.txt")):
        print(path)
        if path.stem.startswith("Deck - "):
            path = path.rename(path.with_stem(path.stem.removeprefix("Deck - ")))

        with path.open("r") as fp:
            lines = fp.read().splitlines()

        deck = pd.DataFrame([pattern.match(line).groupdict() for line in lines if len(line)])
        deck["foil"] = deck["foil"].map(lambda x: "foil" if x else "regular")

        deck["deck"] = path.stem
        deck_list.append(deck)

    combined_cards = pd.concat(available_cards)
    combined_cards["quantity"] = combined_cards["quantity"].astype(int)

    combined_decks = pd.concat(deck_list)
    combined_decks["quantity"] = combined_decks["quantity"].astype(int)

    all_combined = pd.concat([combined_cards, combined_decks])

    all_combined = all_combined.groupby(NEW_COLS[:-1], as_index=False, dropna=False).agg(
        quantity=("quantity", "sum"),
        decks=("deck", list),
    )

    diffs = collection.merge(all_combined, how="outer", on=NEW_COLS, indicator=True)
    diffs = diffs.loc[diffs._merge != "both"]

    diffs.sort_values("decks", inplace=True)
    diffs.reset_index(drop=True, inplace=True)

    out_path = OUT_PATH / "diffs.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    diffs.to_csv(out_path.as_posix())
    print(diffs)

    for deck in deck_list:
        deck_name = deck.loc[0, "deck"]
        out_dir = OUT_PATH / deck_name
        shutil.rmtree(out_dir, ignore_errors=True)
        if not deck["set_id"].isna().any():
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        owned_path = out_dir / "owned.txt"
        missing_path = out_dir / "missing.txt"

        owned_cards = combined_cards.loc[combined_cards["card"].isin(deck["card"])].copy()
        owned_cards.sort_values(["deck", "card", "set_id"], inplace=True)
        owned_cards["formatted"] = format_entries(owned_cards, deck, deck_info=True)
        # print(owned_cards)

        missing_cards = deck.loc[~deck["card"].isin(owned_cards["card"])]
        missing_cards.sort_values(["deck", "card", "set_id"], inplace=True)
        missing_cards["formatted"] = format_entries(missing_cards, deck, deck_info=False)
        # print(missing_cards)

        with owned_path.open("w") as fp:
            fp.write("\n".join(owned_cards["formatted"]) + "\n")

        with missing_path.open("w") as fp:
            fp.write("\n".join(missing_cards["formatted"]) + "\n")


if __name__ == "__main__":
    main()
