from src.app.config import Config
from src.background.background_process import BackgroundProcess
from src.context import Context, ContextManager
import time
import os
from dotenv import load_dotenv
from src.databaseHelper.sql_db import UserProfileDatabase

background_process = BackgroundProcess()

load_dotenv()
profiling_interval = os.getenv(key='BACKGROUND_PROFILING_INTERVAL', default=200)
summery_interval = os.getenv(key='BACKGROUND_SUMMERY_INTERVAL', default=200)


def add_background_tasks(all_messages, config: Config, api_key: str):
    context = Context(messages=all_messages, config=config, api_key=api_key)
    conversation_id = context.get_conversation_id()
    # summery
    summery_job_id = f"summery-{conversation_id}{api_key}"
    background_process.debounce_run(
        job_id=summery_job_id,
        function=_background_summarizer,
        second_after=summery_interval,
        # functions args
        config=config,
        context=context,
        api_key=api_key
    )
    # profile
    profile_job_id = f"profile-{conversation_id}{api_key}"
    background_process.debounce_run(
        job_id=profile_job_id,
        function=_background_profiling,
        second_after=profiling_interval,
        # functions args
        config=config,
        context=context,
        api_key=api_key
    )


def _background_summarizer(config: Config, context: Context, api_key: str):
    # create summery of the conversation
    summery_prompt = config.chat_summariser
    context_manager = ContextManager(messages=[], config=config, api_key=api_key)
    summery_json = context_manager.render_prompt(
        prompt=summery_prompt,
        context=context,
        output_json=True
    )
    print(f"summery json: {summery_json}")

    # extract all values
    prompt = context.message_to_prompt()
    description = summery_json.get("description", "")
    chat_flow = summery_json.get("chat_flow", "")
    information = summery_json.get("information", "")

    # make embedding for each
    v_description = context_manager.llm_manager.get_embed(description)
    v_chat_flow = context_manager.llm_manager.get_embed(chat_flow)
    v_information = context_manager.llm_manager.get_embed(information)
    v_prompt = context_manager.llm_manager.get_embed(prompt)

    # prepare the payload
    vector = {
        "description": v_description,
        "chat_flow": v_chat_flow,
        "information": v_information,
        "prompt": v_prompt
    }
    payload = {
        "prompt": prompt,
        "description": description,
        "chat_flow": chat_flow,
        "information": information,
        "updated": time.time(),
        "api_key": api_key,
        "model_name": config.model_name
    }

    # upload summery
    conversation_id = context.get_conversation_id()
    context.vectorDB.upsert_chat_summery(
        vector=vector,
        payload=payload,
        conversation_id=conversation_id
    )


def _background_profiling(config: Config, context: Context, api_key: str):
    # generate user profile
    user_profiling_prompt = config.user_profiling
    context_manager = ContextManager(messages=[], config=config, api_key=api_key)
    count = context_manager.context.vectorDB.count_collection(config.vector_database.collection_name)
    print(f"count: {count}")
    user_profile_text = context_manager.render_prompt(
        prompt=user_profiling_prompt,
        context=context,
        output_json=False
    )
    print(f"user_profile_text:{user_profile_text}")
    # save profile to sql database
    user_profile_database = UserProfileDatabase()
    user_profile_database.update_profile(
        model_name=user_profiling_prompt.model,
        api_key=api_key,
        content=user_profile_text
    )
