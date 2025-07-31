Run Python scripts using the conda environment `idv-torchserve-dev` to ensure all dependencies are correctly installed. Do not use pip. Use conda for any environment changes.

After completing your changes, as part of your final summary, provide a suggested commit message that describes the changes made. The commit message should be concise and follow the format: `feat: <description>` for new features, `fix: <description>` for bug fixes, or `docs: <description>` for documentation updates. Make sure to wrap any code snippets in the commit message with backticks (``).

Always make use of type annotations in Python code. If adding `# type: ignore` is needed to avoid linter erorrs, add a further comment explaining why this was necessary. For example:

```
split: list[pd.DataFrame]  = train_test_split( # type: ignore # The result will match the inputs (`pd.DataFrame`)
                self.files,
                test_size=(1 - load_fraction),
                stratify=self.files["label"], # type: ignore # The label type is irrelevant here
            )
```

Functions/methods should be *always* given docstrings in the following style, detailing their arguments, return values, and exceptions raised.
```
def get_stratified_subsets(
    self,
    test_size: float = 0.2,
    random_state: int = 113,
) -> tuple["CustomSubset", "CustomSubset"]:
    """Split the dataset into stratified training and validation subsets.

    Args:
        test_size (float, optional): The fraction of the dataset to use for validation.
        random_state (int, optional): The random seed for reproducibility.
        
    Returns:
        tuple: A tuple containing:
            - A `CustomSubset` for training.
            - A `CustomSubset` for validation.
            
    Raises:
        ValueError: If the DataFrame does not contain a 'label' column.

    """
```

Classes should *always* be given docstrings in the following format, detailing their attributes.
```
class CustomDataset(Dataset):
    """A base class for custom datasets.

    Provides common functionality, such as loading data from a folder,
    transforming the data, and splitting the dataset into subsets.

    Attributes:
        rootdir (Path): The root directory of the dataset.
        files (pd.DataFrame): A DataFrame containing the file paths and labels.
        transform (nn.Module | None): A transform to apply to the data.
        load_fraction (float): The fraction of the dataset to load.

    """
    
    rootdir: Path
    files: pd.DataFrame
    transform: nn.Module | None
    load_fraction: float
```

Note that there should be a blank line after the last section of a docstring (Returns, Raises, etc.).