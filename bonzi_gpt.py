from transformers import GPT2LMHeadModel, GPT2Tokenizer, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from datasets import load_dataset
import os
import pyttsx3
import threading


class BonziGPT:
    """A class for creating Bonzi's GPT-2 AI chatbot."""
    def __init__(self, bonzi, text_file, output_dir="bonzi_model"):
        """Initialize the GPT-2 model and tokenizer."""
        self.bonzi = bonzi
        self.settings = bonzi.settings

        # Check if the model has already been trained
        if os.path.exists(output_dir):
            self.model = GPT2LMHeadModel.from_pretrained(output_dir)
        else:
            self.model = GPT2LMHeadModel.from_pretrained("gpt2")

        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # Train the model if it hasn't been trained
        if not os.path.exists(output_dir):
            self.fine_tune_gpt(text_file, output_dir)

        # Initialize the text-to-speech thread and engine
        self.tts_thread = None
        self.engine = pyttsx3.init()

    def get_response(self, text):
        """Get a response from Bonzi's GPT-2 chatbot after processing the input text."""
        # Convert the input text to tokenizer format
        user_input = self.tokenizer.encode(text, return_tensors="pt")

        attention_mask = user_input.ne(self.tokenizer.pad_token_id).float()  # model won't focus on padding tokens

        temperature = min(1.0, max(0.7, len(text) / 100))  # dynamic temperature based on input length, min 0.7, max 1.0

        bonzi_output = self.model.generate(user_input,
                                           max_length=60,
                                           num_return_sequences=1,
                                           do_sample=True,  # choose words on probability, causing more diversity
                                           temperature=temperature,  # randomness of output, 1 = maximum, 0 = minimum
                                           top_p=0.9,  # cumulative probability of the most likely tokens, more natural
                                           attention_mask=attention_mask,
                                           pad_token_id=self.tokenizer.eos_token_id)

        response = self.tokenizer.decode(bonzi_output[0], skip_special_tokens=True)

        # Start a thread to convert the response to speech while the main program continues
        self.tts_thread = threading.Thread(target=self.text_to_speech, args=(response,))  # use function and argument
        self.tts_thread.daemon = True  # thread will close when the main program closes
        self.tts_thread.start()

        return response

    def text_to_speech(self, response):
        """Convert the AI's response into speech."""

        # Get list of voices
        voices = self.engine.getProperty("voices")

        # Set the voice to Microsoft David
        for voice in voices:
            if "david" in voice.name.lower():
                self.engine.setProperty("voice", voice.id)
                break

        # Set the rate and volume
        self.engine.setProperty("rate", self.bonzi.settings.rate)  # words per minute
        self.engine.setProperty("volume", self.bonzi.settings.volume)  # volume level 0.0 to 1.0

        # Convert the text to speech
        self.engine.say(response)

        # Use runAndWait(), it is in a thread, so it shouldn't block the main program
        self.engine.runAndWait()

        # Remove the chat bubble once TTS finishes.
        self.bonzi.chat_bubble = None

        # Set processing_tts to False and allow another response
        self.bonzi.input_box.processing_tts = False

    def fine_tune_gpt(self, text_file, output_dir="./"):
        """Train the GPT-2 model on a text file."""
        tokenizer = self.tokenizer
        model = self.model

        # Prepare the dataset
        dataset = load_dataset("text", data_files=text_file)
        tokenized_dataset = dataset.map(lambda examples:
                                        {"input_ids": [tokenizer(text)["input_ids"]
                                         for text in examples["text"] if text.strip() != ""]},
                                        batched=True,
                                        remove_columns=["text"],
                                        )

        # Take out the None values
        tokenized_dataset = tokenized_dataset.filter(lambda x: x is not None)

        # Put data in format for language modeling
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,  # Not using masked language modeling
        )

        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,  # output directory
            overwrite_output_dir=True,  # overwrite the content of the output directory
            num_train_epochs=2,  # number of training epochs, or number of times the model will see the dataset
            per_device_train_batch_size=1,  # batch size for training, number of samples per forward/backward pass
            save_steps=10_000,  # number of steps before saving
            save_total_limit=2,  # limit the number of checkpoints, or saved models
            learning_rate=5e-5,  # standard learning rate to optimize the model
        )

        # Create the trainer using the model, training arguments, data collator, and dataset.
        trainer = Trainer(
            model=model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=tokenized_dataset["train"],
        )

        # Call the training method
        trainer.train()

        # Save the model
        trainer.save_model(output_dir)




