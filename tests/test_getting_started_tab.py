from mcsas3gui.gui.getting_started_tab import GettingStartedTab


class _FakeFileSelectionWidget:
    def __init__(self) -> None:
        self.calls = []

    def clear_all_files(self) -> None:
        self.calls.append(("clear_all_files",))

    def add_file_to_table(self, file_name: str) -> None:
        self.calls.append(("add_file_to_table", file_name))


class _FakeOptimizationTab:
    def __init__(self) -> None:
        self.file_selection_widget = _FakeFileSelectionWidget()


def test_apply_optimization_files_clears_previous_files_before_adding_template_files(tmp_path):
    tab = GettingStartedTab.__new__(GettingStartedTab)
    tab.main_path = tmp_path
    tab.optimization_tab = _FakeOptimizationTab()

    tab._apply_optimization_files(["data/first.dat", "data/second.dat"])

    assert tab.optimization_tab.file_selection_widget.calls == [
        ("clear_all_files",),
        ("add_file_to_table", str(tmp_path / "data/first.dat")),
        ("add_file_to_table", str(tmp_path / "data/second.dat")),
    ]


def test_apply_optimization_files_clears_previous_files_when_template_has_no_optimization_files(tmp_path):
    tab = GettingStartedTab.__new__(GettingStartedTab)
    tab.main_path = tmp_path
    tab.optimization_tab = _FakeOptimizationTab()

    tab._apply_optimization_files([])

    assert tab.optimization_tab.file_selection_widget.calls == [("clear_all_files",)]
