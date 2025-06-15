import chainlit as cl

from ..utils.logger import logger
from ..config import ui_config


class SidePanel:
    """Component for the analysis side panel (mindmap/tree search)"""

    def __init__(self):
        self.enabled = ui_config.enable_analysis_panel
        logger.info(f"SidePanel component initialized (enabled: {self.enabled})")

    async def setup_panel(self):
        """Set up the side panel with placeholder content"""
        if not self.enabled:
            logger.debug("Side panel is disabled")
            return

        try:
            # Create a custom element for the side panel
            # This will be displayed in the right sidebar
            content = """
            <div style="padding: 20px; background-color: #f8f9fa; border-radius: 8px; height: 100%;">
                <h3 style="margin-top: 0; color: #333;">🧠 Conversation Analysis</h3>
                
                <div style="margin-top: 20px;">
                    <p style="color: #666; font-size: 14px;">
                        <em>Coming soon: Real-time conversation analysis with mindmap and tree search visualization.</em>
                    </p>
                </div>
                
                <div style="margin-top: 30px; padding: 15px; background-color: #e9ecef; border-radius: 6px;">
                    <h4 style="margin-top: 0; color: #495057; font-size: 16px;">📊 Features in Development:</h4>
                    <ul style="color: #6c757d; font-size: 14px; padding-left: 20px;">
                        <li>Interactive mindmap of conversation topics</li>
                        <li>Semantic search through chat history</li>
                        <li>Topic clustering and analysis</li>
                        <li>Conversation flow visualization</li>
                        <li>Key insights extraction</li>
                    </ul>
                </div>
                
                <div style="position: absolute; bottom: 20px; left: 20px; right: 20px;">
                    <p style="color: #adb5bd; font-size: 12px; text-align: center;">
                        Analysis panel v0.1 (Preview)
                    </p>
                </div>
            </div>
            """

            # Set the HTML element for the sidebar
            await cl.Message(
                content="",
                elements=[
                    cl.Html(name="analysis_panel", content=content, display="side")
                ],
            ).send()

            logger.info("Side panel setup completed")

        except Exception as e:
            logger.error(f"Failed to setup side panel: {e}", exc_info=True)

    async def update_analysis(self, chat_id: str, messages: list):
        """Update the analysis panel with new data (placeholder for future implementation)"""
        if not self.enabled:
            return

        logger.debug(
            f"Analysis update called for chat {chat_id} with {len(messages)} messages"
        )
        # Future implementation will update the mindmap/tree visualization here

    async def show_mindmap(self, data: dict):
        """Display mindmap visualization (placeholder for future implementation)"""
        if not self.enabled:
            return

        logger.debug(
            "Mindmap display requested",
            extra={"data_keys": list(data.keys()) if data else []},
        )
        # Future implementation will render the mindmap here

    async def show_search_results(self, query: str, results: list):
        """Display search results in the panel (placeholder for future implementation)"""
        if not self.enabled:
            return

        logger.debug(
            f"Search results display requested for query: {query}",
            extra={"result_count": len(results)},
        )
        # Future implementation will display search results here
