 

# Config json structure 
- model_name
- description
- template_function_path # py file with functions for template
- system_prompt: Prompt # default system prompt if no route not found
  - name
  - file_name
  - model
- context_summariser: Prompt # make summery if context gets bigger
  - name
  - file_name
  - model
- user_profiling: Prompt # make profile of user reading old context
  - name
  - file_name
  - model
- embedding_model # default vector database
  - name
  - api_type
  - base_url
  - api_key
  - model_key
- vector_database
  - type
  - host
  - port
  - collection_name # default chat collection
  - score_threshold
  - default_limit # limit similarity result
- models [Model]
  - name
  - api_type
  - base_url
  - api_key
  - model_id
- routing_prompts # use system_prompt if no routing found
  - prompt # prompt to generate routing json 
    - name
    - file_name
    - model
    - routes [Prompt]
      - name
      - file_name
      - model


# Template function
in template file write `{{current_time( context )}}` with `context` variable present
and in the `TemplateFunctions.py` file each function need `context` variable too 
```python
def current_time(context):
    pass
```

## Cache function call 
Some function call may call external function over and over for API call , so it's better to cache the value for sometime
to cache function output in the template file specify second , `{{current_weather( context, cache_ttl=60*60 )}}`


## routing prompts 
Routing prompt needs to output json with "route" value , example
```json
{
  "route": "basic"
}
```

## Context summariser Prompt
extra variable send to "context_summariser" prompt
```
{{ full_context }}
```

## System prompt
extra variable send to "system_prompt" prompt
```
{{ context_summery }}
```

