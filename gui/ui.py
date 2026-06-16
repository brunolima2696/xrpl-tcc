from __future__ import annotations
import os
from datetime import datetime
from nicegui import ui
from runner import run_script
from dotenv import load_dotenv
load_dotenv()

PORT=os.getenv("GUI_PORT")
os.environ["PYDANTIC_DISABLE_PLUGINS"] = "__all__"

class RoleMenu:
    def __init__(
        self,
        title: str,
        icon: str,
        main_actions: list[tuple[str, str]],
        optional_actions: list[tuple[str, str]] | None = None,
        open_by_default: bool = False,
    ) -> None:
        self.title = title
        self.main_actions = main_actions
        self.optional_actions = optional_actions or []

        self.is_running = False
        self.status_text = "Idle"
        self.last_exit_code = "-"
        self.last_run = "Never"

        self.main_buttons: list = []
        self.optional_buttons: list = []

        with ui.card().classes("w-full"):
            with ui.expansion(self.title, icon=icon, value=open_by_default).classes("w-full"):
                with ui.column().classes("w-full gap-3"):
                    ui.label(
                        
                    ).classes("text-xs text-gray-400")

                    with ui.row().classes("w-full gap-6 flex-wrap"):
                        self.status_label = ui.label(f"Status: {self.status_text}")
                        # self.exit_code_label = ui.label(f"Last exit code: {self.last_exit_code}")
                        self.last_run_label = ui.label(f"Last run: {self.last_run}")

                    ui.label("Ações principais").classes("text-sm font-medium")

                    with ui.column().classes("w-full gap-2"):
                        for label, script_name in self.main_actions:
                            button = ui.button(
                                label,
                                on_click=self._make_execute_handler(
                                    script_name=script_name,
                                    action_label=label,
                                    optional=False,
                                ),
                            ).props("color=primary")
                            button.classes("w-full justify-start")
                            self.main_buttons.append(button)

                    if self.optional_actions:
                        with ui.expansion("Ações opcionais", icon="tune", value=False).classes("w-full"):
                            with ui.column().classes("w-full gap-2 pt-2"):
                                for label, script_name in self.optional_actions:
                                    button = ui.button(
                                        label,
                                        on_click=self._make_execute_handler(
                                            script_name=script_name,
                                            action_label=label,
                                            optional=True,
                                        ),
                                    ).props("color=secondary")
                                    button.classes("w-full justify-start")
                                    self.optional_buttons.append(button)

                    self.log = ui.log(max_lines=300).classes("w-full h-64 border rounded")

    def _make_execute_handler(self, script_name: str, action_label: str, optional: bool):
        async def handler() -> None:
            await self.execute_action(script_name, action_label, optional)

        return handler

    def refresh_info(self) -> None:
        self.status_label.text = f"Status: {self.status_text}"
        # self.exit_code_label.text = f"Last exit code: {self.last_exit_code}"
        self.last_run_label.text = f"Last run: {self.last_run}"

        self.status_label.update()
        # self.exit_code_label.update()
        self.last_run_label.update()

    async def execute_action(self, script_name: str, action_label: str, optional: bool) -> None:
        if self.is_running:
            ui.notify(f"{self.title} já possui um script em execução.", color="warning")
            return

        self.is_running = True
        self.status_text = "Running optional" if optional else "Running"
        self.last_exit_code = "-"
        self.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.refresh_info()

        for button in self.main_buttons:
            button.disable()
        for button in self.optional_buttons:
            button.disable()

        kind = "OPTIONAL" if optional else "MAIN"

        self.log.push("")
        self.log.push("=" * 60)
        self.log.push(f"[{self.last_run}] Starting {kind} action: {action_label} ({script_name})")

        try:
            exit_code = await run_script(script_name, self.log.push)
            self.last_exit_code = str(exit_code)
            self.status_text = "Success" if exit_code == 0 else "Failed"
            self.log.push(f"{action_label} finished.")

        except Exception as exc:
            self.status_text = "Error"
            self.last_exit_code = "exception"
            self.log.push(f"[EXCEPTION][{kind}] {exc}")

        finally:
            self.is_running = False
            self.refresh_info()

            for button in self.main_buttons:
                button.enable()
            for button in self.optional_buttons:
                button.enable()


def build_ui() -> None:
    ui.page_title("XRPL Local Roles Panel")

    dark = ui.dark_mode()
    dark.enable()
    ui.button("CHANGE THEME", on_click=dark.toggle)

    with ui.column().classes("w-full max-w-5xl mx-auto p-6 gap-4"):
        ui.label("XRPL Local Roles Panel").classes("text-2xl font-bold")
        ui.label(
            "Local interface for roles execution."
        ).classes("text-sm text-gray-400")

        RoleMenu(
            "Issuer",
            "badge",
            main_actions=[
                ("Define Local DID Data", "issuer/define_local_did_data.py"),
                ("Create DID Document", "issuer/xrpl_did/create_did_document.py"),
                ("Create Verifiable Credential", "issuer/create_verifiable_credential.py"),
                ("Issue Credential to XRPL","issuer/xrpl_credential/issue_credential.py"),
            ],
            optional_actions=[
                ("Check DID", "issuer/xrpl_did/check_did.py"),
                ("Delete DID", "issuer/xrpl_did/delete_did.py"),
                ("Delete Credential","issuer/xrpl_credential/delete_credential.py"),
            ],
            open_by_default=False,
        )

        RoleMenu(
            "Holder",
            "person",
            main_actions=[
                ("Define Local DID Data", "holder/define_local_did_data.py"),
                ("Create DID Document", "holder/xrpl_did/create_did_document"),
                ("Accept XRPL Credential", "holder/xrpl_credential/accept_credential.py"),
                ("Create Verifiable Presentation","holder/create_verifiable_presentation.py"),
            ],
            optional_actions=[
                ("Check DID", "holder/xrpl_did/check_did.py"),
                ("Delete DID", "holder/xrpl_did/delete_did.py"),
                ("Delete Credential","holder/xrpl_credential/delete_credential.py"),
            ],
            open_by_default=False,
        )

        RoleMenu(
            "Verifier",
            "verified",
            main_actions=[
                ("Verify VP Signature", "verifier/verify_vp_signature.py"),
                ("Verify XRPL Credential", "verifier/verify_xrpl_credential.py"),
            ],
            optional_actions=[
                ("Verify VC Signature", "verifier/verify_vc_signature.py"),
            ],
            open_by_default=False,
        )


build_ui()

ui.run(
    title="XRPL Roles Panel",
    reload=False,
    port=PORT
)