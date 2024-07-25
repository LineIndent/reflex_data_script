import json
import os
import click
import sys


def validate_file_path(ctx, param, file_path):
    if file_path.lower() == "q":
        click.echo("Exiting...")
        sys.exit()
    if not os.path.exists(file_path):
        raise click.BadParameter(f"The file at path '{file_path}' does not exist.")
    if not file_path.endswith((".csv", ".json")):
        raise click.BadParameter("The file must be a .csv or .json file.")
    return file_path


def process_data_file(file_path: str):
    with open(file_path, "r") as file:
        obj = json.load(file)

    main_data = obj
    number_of_rows = len(obj)
    column_names = list(obj[0].keys()) if obj else []
    return main_data, number_of_rows, column_names


@click.command()
@click.option(
    "--data-path",
    prompt="Please provide the path to your data file (.csv or .json)",
    callback=validate_file_path,
)
def cli(data_path):
    main_data, number_of_rows, column_names = process_data_file(data_path)

    click.echo(f"Your data file at '{data_path}' has been successfully validated.")

    state_name = click.prompt("What would you like to call the STATE class?", type=str)
    if state_name.lower() == "q":
        click.echo("Exiting...")
        sys.exit()
    click.echo(f"State name saved as '{state_name}'.")

    output_file_name = click.prompt(
        "What would you like to call the output file?", type=str
    )
    if output_file_name.lower() == "q":
        click.echo("Exiting...")
        sys.exit()
    if not output_file_name.endswith(".py"):
        output_file_name += ".py"

    output_file_path = click.prompt(
        "Please provide the path to place the output file", type=str
    )
    if output_file_path.lower() == "q":
        click.echo("Exiting...")
        sys.exit()

    full_output_path = os.path.join(output_file_path, output_file_name)
    click.echo(f"Output file will be saved as '{full_output_path}'.")

    with open(full_output_path, "w") as f:
        f.write(
            f"""import reflex as rx

class {state_name}(rx.State):
    main_data: list[dict[str, str]] = {main_data}
    number_of_rows: int = {number_of_rows}
    column_names: list[str] = {column_names}
    current_limit: int = 10
    limits: list[str] = ["10", "20", "50"]
    offset: int = 0
    current_page: int = 1
    total_pages: int = (number_of_rows + current_limit - 1) // current_limit
    paginated_data: list[dict[str, str]]

    def paginate(self):
        start = self.offset
        end = start + self.current_limit
        self.paginated_data = self.main_data[start:end]
        self.current_page = (self.offset // self.current_limit) + 1

    def delta_limit(self, limit: str):
        self.current_limit = int(limit)
        self.offset = 0
        self.total_pages = (
            self.number_of_rows + self.current_limit - 1
        ) // self.current_limit
        self.paginate()

    def previous(self):
        if self.offset >= self.current_limit:
            self.offset -= self.current_limit
        else:
            self.offset = 0

        self.paginate()

    def next(self):
        if self.offset + self.current_limit < self.number_of_rows:
            self.offset += self.current_limit

        self.paginate()

def create_table_header(title: str):
    return rx.table.column_header_cell(title)

def create_query_rows(data: dict[str, str]):
    def fill_rows_with_data(data_):
        return rx.table.cell(
            data_[1],
            cursor="pointer",
        )

    return rx.table.row(
        rx.foreach(data, fill_rows_with_data),
        _hover={{"bg": rx.color(color="gray", shade=4)}},
    )

def create_pagination():
    return rx.hstack(
        rx.hstack(
            rx.text("Entries per page", weight="bold"),
            rx.select(
                {state_name}.limits, default_value="10", on_change={state_name}.delta_limit
            ),
            align_items="center",
        ),
        rx.hstack(
            rx.text(
                f"Page {{ {state_name}.current_page }}/{{ {state_name}.total_pages }}",
                width="100px",
                weight="bold",
            ),
            rx.chakra.button_group(
                rx.icon(
                    tag="chevron-left", on_click={state_name}.previous, cursor="pointer"
                ),
                rx.icon(tag="chevron-right", on_click={state_name}.next, cursor="pointer"),
                is_attached=True,
            ),
            align_items="center",
            spacing="1",
        ),
        align_items="center",
        spacing="4",
    )

def render_output():
    return rx.center(
        rx.vstack(
            create_pagination(),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.foreach({state_name}.column_names, create_table_header)
                    ),
                ),
                rx.table.body(
                    rx.foreach({state_name}.paginated_data, create_query_rows)
                ),
                width="100%",
                variant="surface",
                size="1",
            ),
            width="100%",
            overflow="auto",
            padding="2em 2em",
        ),
        flex="60%",
        bg=rx.color_mode_cond(
            "#faf9fb",
            "#1a181a",
        ),
        border_radius="10px",
        overflow="auto",
    )
"""
        )

    click.echo("The output file has been created successfully.")


if __name__ == "__main__":
    cli()
