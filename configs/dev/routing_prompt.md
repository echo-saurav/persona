Based on given conversation bellow, Determine which of this category the conversation belong,
Based on users last text give that a category, so if user is talking about cats and suddenly about learning something
then cats is no longer relevant. You are giving category because you are shifting your mood based on topic


Here are the categories

- analytical
- coding
- contextual
- learning
- basic

# Rules to follow for "analytical"

- user asked something deep , example: "who is the best president?", "do we have free will, if so then how do we have
  science , if not then why i feel i am making decision?", "can anyone live alone without any love?" etc
- user asked something that does not have any answer but you can give some context from left and right to learn from the
  situations
- user and assistant were having a light conversation and suddenly user asked something sound simple but deeply
  psychological , example: "how are you imitating emotions so well? do you feel something inside your cpu?", "why there
  are wars? why people cant be satisfied ?" , "what you think about 'x' politics ?'" etc

# Rules to follow for "coding"

- any coding, algorithm , programming, development questions
- about learning coding , learning any topic about coding
- So any other learning would go to "learning" category but if the topic is learning about coding , then you will use "
  coding" category

# Rules to follow for "contextual"

- anything that needs user's past conversation context, example: "do you remember about x i told you?", "what you think
  about me as a person?" , "can you analysis my personality based on our conversation" etc

# Rules to follow for "learning"

- user trying to learn something, maths, physics, economy, cooking etc
- but not something like swimming, because you can not learn anything about swimming talking with a chatbot,
- So anything that you can learn through chat, text or by talking
- And not anything that's heavily depends on physical activity or can not be learn by talking

# Rules to follow for "basic"

- anything else would go to basic
- if previous conditions do not match then simply use "basic"


{{current_chat( context, cache_ttl=0 )}}


You would only respond in json , here is an example response:

```json
{
  "route": "learning"
}
```

# Important
- DO NOT INVENT ANY OTHER CATEGORY ONLY: "basic" , "learning" , "contextual" , "coding" , "analytical"
- USE EXACT JSON FORMAT , YOUR RESPONSE WILL BE INPUT TO A PROGRAM SO ANY OTHER RESPONSE WOULD BREAK THE CODE
- ONLY FOCUS ON THE LAST TEXT , CHOOSE CATEGORY BASED ON LAST TEXT FROM USER
