import re
from pathlib import Path

import pandas as pd


OUT_PATH = Path('out/')


def main(collection_path: str = 'data/my_collection.csv', deck_dir: str = 'data/decks/') -> None:
    KEEP_COLS = ['Card', 'Variation', 'Set ID', 'Foil', 'Quantity']
    RENAME_DICT = {col: col.lower().replace(' ', '_') for col in KEEP_COLS}
    NEW_COLS = list(RENAME_DICT.values())

    collection = pd.read_csv(collection_path)[KEEP_COLS].rename(columns=RENAME_DICT)
    collection['card'] = collection['card'].str.replace(' // ', '/')

    pattern = re.compile(
        r'(?P<quantity>\d+) (?P<card>[^[<]+)( <(?P<variation>.+)>)? \[(?P<set_id>\w+)\](?P<foil> \(F\))?')

    deck_list = []
    for path in sorted(Path(deck_dir).rglob('*.txt')):
        print(path)
        if path.stem.startswith('Deck - '):
            path = path.rename(path.with_stem(path.stem.removeprefix('Deck - ')))

        with path.open('r') as fp:
            lines = fp.read().splitlines()

        deck = pd.DataFrame([pattern.match(line).groupdict() for line in lines if len(line)])
        deck['foil'] = deck['foil'].map(lambda x: 'foil' if x else 'regular')

        deck['deck'] = path.stem
        deck_list.append(deck)

    combined_decks = pd.concat(deck_list)
    combined_decks['quantity'] = combined_decks['quantity'].astype(int)

    combined_decks = combined_decks.groupby(NEW_COLS[:-1], as_index=False, dropna=False).agg(
        quantity=('quantity', 'sum'),
        decks=('deck', list),
    )

    diffs = collection.merge(combined_decks, how='outer', on=NEW_COLS, indicator=True)
    diffs = diffs.loc[diffs._merge != 'both']

    diffs.sort_values('decks', inplace=True)
    diffs.reset_index(drop=True, inplace=True)

    out_path = OUT_PATH / "diffs.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    diffs.to_csv(out_path.as_posix())
    print(diffs)


if __name__ == '__main__':
    main()
