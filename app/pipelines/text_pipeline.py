from typing import Any
from langdetect import detect

from app.llm.conversation_memory import ConversationReminder
from app.pipelines import BaseConversationPipeline


class TextPipeline(BaseConversationPipeline):
    """This pipeline orchestrates the full text-to-text flow."""

    async def process_conversation(
        self, user_input_text: str, chat_memory: ConversationReminder, user_profile: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Orchestrates the full text-to-text conversation flow.

        The method executes the following steps:
        1. Detects if the topic has changed and resets context if needed
        2. Prepares prompts including conversation history for the LLM
        3. Sends prompts to the LLM and retrieves the generated response
        4. Updates the conversation context and state

        :user_input_text: Text input from the user
        :chat_memory: ConversationReminder instance containing the conversation history
        :user_profile: Optional dictionary containing user profile information (e.g., name, preferences)
        :returns: A dictionary containing:
            language, user_input_text, model_output_text, parsed_profile
        """
        language = detect(user_input_text)
        self.logger.info(f"Detected language: {language}")

        # Topic detection
        if self.topic_detector.is_new_topic(self.state.summary, user_input_text):
            self.logger.info("Topic change detected. Resetting conversation state.")
            self.state.clear()
            chat_memory.clear()

        # Prompt construction
        prompts = self.prepare_prompts_to_llm(language, user_input_text, chat_memory, user_profile)
        for prompt in prompts:
            self.logger.debug(f"\nEnqueued prompt: {prompt}")

        # LLM output preparing
        model_output_text = await self.llm.chat(prompts)
        self.logger.info(f"[LLM] Response:\n\t{model_output_text}")
        chat_memory.add_user_message(user_input_text)
        chat_memory.add_assistant_message(model_output_text)

        # Conversation context update
        await self.update_conversation_context(language, user_input_text, model_output_text)
        self.logger.info("Conversation context was updated succesfully.")
        parsed_profile = await self.update_user_profile(chat_memory, user_profile)

        return {
            "language": language,
            "user_input_text": user_input_text,
            "model_output_text": model_output_text,
            "parsed_profile": parsed_profile,
        }
