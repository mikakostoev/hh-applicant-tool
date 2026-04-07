from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Checkbox, Collapsible, Input, Select, Static, TextArea

from ..command_builder import CommandBuilder
from .base import AppScreen


AI_FILTER_OPTIONS = [
    ("Disabled", ""),
    ("heavy", "heavy"),
    ("light", "light"),
]

ORDER_BY_OPTIONS = [
    ("Default", ""),
    ("publication_time", "publication_time"),
    ("salary_desc", "salary_desc"),
    ("salary_asc", "salary_asc"),
    ("relevance", "relevance"),
    ("distance", "distance"),
]


class ApplyFormScreen(AppScreen):
    screen_title = "apply-vacancies"
    screen_subtitle = "Build argv for apply-vacancies and run the existing CLI command"

    def compose_content(self) -> ComposeResult:
        with VerticalScroll(classes="form-scroll"):
            yield Static("Core arguments", classes="section-title")
            yield Input(placeholder="Resume ID", id="resume-id")
            yield Input(placeholder="Search query", id="search")
            yield Input(placeholder="Letter file path", id="letter-file")
            yield Checkbox("Force message", id="force-message")
            yield Checkbox("Use AI for message generation", id="use-ai")
            yield Select(AI_FILTER_OPTIONS, value="", allow_blank=False, id="ai-filter")
            yield Input(value="40", placeholder="AI rate limit", id="ai-rate-limit")
            yield TextArea(
                text="Напиши сопроводительное письмо для отклика на эту вакансию. Не используй placeholder'ы, твой ответ будет отправлен без обработки.",
                id="system-prompt",
                classes="multi-line",
            )
            yield TextArea(
                text="Сгенерируй сопроводительное письмо не более 5-7 предложений от моего имени для вакансии",
                id="message-prompt",
                classes="multi-line",
            )
            yield Input(value="20", placeholder="Total pages", id="total-pages")
            yield Input(value="100", placeholder="Results per page", id="per-page")
            yield Checkbox("Send email", id="send-email")
            yield Checkbox("Skip tests", id="skip-tests")
            yield Checkbox("Dry run", id="dry-run")
            yield Input(placeholder="Excluded filter regex", id="excluded-filter")
            yield Input(placeholder="Max responses", id="max-responses")

            with Collapsible(title="Search filters", collapsed=True):
                yield Select(ORDER_BY_OPTIONS, value="", allow_blank=False, id="order-by")
                yield Input(placeholder="Experience", id="experience")
                yield Input(placeholder="Schedule", id="schedule")
                yield TextArea(placeholder="Employment values, one per line", id="employment", classes="multi-line")
                yield TextArea(placeholder="Area IDs, one per line", id="area", classes="multi-line")
                yield TextArea(placeholder="Metro IDs, one per line", id="metro", classes="multi-line")
                yield TextArea(placeholder="Professional role IDs, one per line", id="professional-role", classes="multi-line")
                yield TextArea(placeholder="Industry IDs, one per line", id="industry", classes="multi-line")
                yield TextArea(placeholder="Employer IDs, one per line", id="employer-id", classes="multi-line")
                yield TextArea(placeholder="Excluded employer IDs, one per line", id="excluded-employer-id", classes="multi-line")
                yield Input(placeholder="Currency", id="currency")
                yield Input(placeholder="Salary", id="salary")
                yield Checkbox("Only vacancies with salary", id="only-with-salary")
                yield TextArea(placeholder="Label values, one per line", id="labels", classes="multi-line")
                yield Input(placeholder="Period in days", id="period")
                yield Input(placeholder="Date from (YYYY-MM-DD)", id="date-from")
                yield Input(placeholder="Date to (YYYY-MM-DD)", id="date-to")
                yield Input(placeholder="Top lat", id="top-lat")
                yield Input(placeholder="Bottom lat", id="bottom-lat")
                yield Input(placeholder="Left lng", id="left-lng")
                yield Input(placeholder="Right lng", id="right-lng")
                yield Input(placeholder="Sort point lat", id="sort-point-lat")
                yield Input(placeholder="Sort point lng", id="sort-point-lng")
                yield Checkbox("Disable magic parsing", id="no-magic")
                yield Checkbox("Premium only", id="premium")
                yield TextArea(placeholder="Search fields, one per line", id="search-field", classes="multi-line")

            with Horizontal(classes="action-buttons"):
                yield Button("Run command", id="run-apply", variant="success")
                yield Button("Back", id="go-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go-back":
            self.tui_app.pop_screen()
            return
        if event.button.id != "run-apply":
            return

        args: list[str] = []
        add = CommandBuilder.add_value
        add(args, "--resume-id", self.input_value("resume-id"))
        add(args, "--search", self.input_value("search"))
        add(args, "--letter-file", self.input_value("letter-file"))
        CommandBuilder.add_bool(args, "--force-message", self.checkbox_value("force-message"))
        CommandBuilder.add_bool(args, "--use-ai", self.checkbox_value("use-ai"))
        add(args, "--ai-filter", self.select_value("ai-filter"))
        add(args, "--ai-rate-limit", self.input_value("ai-rate-limit"))
        add(args, "--system-prompt", self.text_area_value("system-prompt"))
        add(args, "--message-prompt", self.text_area_value("message-prompt"))
        add(args, "--total-pages", self.input_value("total-pages"))
        add(args, "--per-page", self.input_value("per-page"))
        CommandBuilder.add_bool(args, "--send-email", self.checkbox_value("send-email"))
        CommandBuilder.add_bool(args, "--skip-tests", self.checkbox_value("skip-tests"))
        CommandBuilder.add_bool(args, "--dry-run", self.checkbox_value("dry-run"))
        add(args, "--excluded-filter", self.input_value("excluded-filter"))
        add(args, "--max-responses", self.input_value("max-responses"))

        add(args, "--order-by", self.select_value("order-by"))
        add(args, "--experience", self.input_value("experience"))
        add(args, "--schedule", self.input_value("schedule"))
        CommandBuilder.add_multi_values(args, "--employment", self.multiline_values("employment"))
        CommandBuilder.add_multi_values(args, "--area", self.multiline_values("area"))
        CommandBuilder.add_multi_values(args, "--metro", self.multiline_values("metro"))
        CommandBuilder.add_multi_values(args, "--professional-role", self.multiline_values("professional-role"))
        CommandBuilder.add_multi_values(args, "--industry", self.multiline_values("industry"))
        CommandBuilder.add_multi_values(args, "--employer-id", self.multiline_values("employer-id"))
        CommandBuilder.add_multi_values(args, "--excluded-employer-id", self.multiline_values("excluded-employer-id"))
        add(args, "--currency", self.input_value("currency"))
        add(args, "--salary", self.input_value("salary"))
        CommandBuilder.add_bool(args, "--only-with-salary", self.checkbox_value("only-with-salary"))
        CommandBuilder.add_multi_values(args, "--label", self.multiline_values("labels"))
        add(args, "--period", self.input_value("period"))
        add(args, "--date-from", self.input_value("date-from"))
        add(args, "--date-to", self.input_value("date-to"))
        add(args, "--top-lat", self.input_value("top-lat"))
        add(args, "--bottom-lat", self.input_value("bottom-lat"))
        add(args, "--left-lng", self.input_value("left-lng"))
        add(args, "--right-lng", self.input_value("right-lng"))
        add(args, "--sort-point-lat", self.input_value("sort-point-lat"))
        add(args, "--sort-point-lng", self.input_value("sort-point-lng"))
        CommandBuilder.add_bool(args, "--no-magic", self.checkbox_value("no-magic"))
        CommandBuilder.add_bool(args, "--premium", self.checkbox_value("premium"))
        CommandBuilder.add_multi_values(args, "--search-field", self.multiline_values("search-field"))

        request = self.tui_app.make_request("apply-vacancies", "apply-vacancies", args=args)
        self.tui_app.run_command(request)
