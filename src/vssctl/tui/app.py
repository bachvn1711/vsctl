from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Label, Static

from .formatting import format_node_details
from .state import BrowserState, matching_nodes
from .tree_view import CatalogTree


class VssBrowserApp(App[None]):
    CSS = """
    #search { dock: top; }
    #body { height: 1fr; }
    #tree-pane { width: 55%; border: solid $accent; }
    #details-pane { width: 45%; border: solid $accent; padding: 1; }
    """
    BINDINGS = [("q", "quit", "Quit"), ("/", "focus_search", "Search"), ("escape", "clear_search", "Clear")]

    def __init__(self, state: BrowserState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Input(placeholder="Search path, name, or description", id="search")
        with Horizontal(id="body"):
            with Vertical(id="tree-pane"):
                yield CatalogTree(self.state.tree.name, id="catalog-tree")
            yield Static("Select a node", id="details-pane")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(CatalogTree).load_domain_tree(self.state.tree)

    def action_focus_search(self) -> None:
        self.query_one(Input).focus()

    def action_clear_search(self) -> None:
        search = self.query_one(Input)
        search.value = ""
        self.query_one(CatalogTree).load_domain_tree(self.state.tree)
        self.query_one(CatalogTree).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        matches = matching_nodes(self.state.tree, event.value)
        visible_paths: set[str] | None = None
        if event.value.strip():
            visible_paths = set()
            for node in matches:
                current = node
                while current is not None:
                    visible_paths.add(current.path)
                    current = current.parent
        self.query_one(CatalogTree).load_domain_tree(self.state.tree, visible_paths)

    def on_tree_node_highlighted(self, event: CatalogTree.NodeHighlighted) -> None:
        if event.node.data is not None:
            self.query_one("#details-pane", Static).update(format_node_details(event.node.data))
