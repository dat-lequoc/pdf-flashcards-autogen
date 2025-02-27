#!/usr/bin/env python3
"""
Script to update flashcards in Supabase with AWS Polly audio.
This script fetches flashcards that don't have phrase_audio, generates it using AWS Polly,
and updates the records in Supabase.
"""

import os
import sys
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from ipa_speech import IPATranscriber
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()

class FlashcardAudioGenerator:
    """Class for generating audio for flashcards and updating Supabase."""
    
    def __init__(self):
        """Initialize the FlashcardAudioGenerator."""
        # Set up Supabase client
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        
        self.supabase = create_client(supabase_url, supabase_key)
        
        # Initialize the IPATranscriber for audio generation
        self.transcriber = IPATranscriber()
        
        # Set the table name
        self.table_name = "flashcards"
    
    def get_all_flashcards(self):
        """Retrieve all flashcards for audio update, regardless of existing audio.
        
        Returns:
            list: List of flashcard records
        """
        try:
            # Query for all flashcards with a phrase (non-null and non-empty)
            response = (self.supabase.table(self.table_name)
                .select("id, phrase")
                .neq("phrase", None)                 # Checks for non-null (IS NOT NULL)
                .neq("phrase", "")                   # Checks for non-empty string
                .execute())
            
            return response.data
        except Exception as e:
            print(f"Error retrieving flashcards: {e}")
            return []
    
    def get_flashcards_without_audio(self):
        """Retrieve flashcards that don't have phrase_audio."""
        try:
            # Query for records where phrase_audio is null or empty,
            # while ensuring the phrase field is non-null and non-empty.
            response = (self.supabase.table(self.table_name)
                .select("id, phrase")
                .neq("phrase", None)
                .neq("phrase", "")
                .or_("phrase_audio.is.null,phrase_audio.eq.''")
                .execute())
            
            return response.data
        except Exception as e:
            print(f"Error retrieving flashcards without audio: {e}")
            return []
    
    def generate_audio_for_flashcards(self, flashcards, voice_id="Joanna"):
        """Generate audio for a batch of flashcards and update Supabase.
        
        Args:
            flashcards (list): List of flashcard records to process
            voice_id (str): AWS Polly voice ID to use for all flashcards
            
        Returns:
            tuple: (success_count, failed_ids)
        """
        success_count = 0
        failed_ids = []
        
        print(f"Processing {len(flashcards)} flashcards...")
        
        # Use tqdm for a progress bar
        for card in tqdm(flashcards, desc="Generating Audio"):
            card_id = card.get("id")
            phrase = card.get("phrase", "")
            
            # Skip if no phrase to process
            if not phrase or phrase.strip() == "":
                tqdm.write(f"Skipping card {card_id}: empty phrase")
                failed_ids.append(card_id)
                continue
            
            try:
                tqdm.write(f"Generating audio for card {card_id}, voice: {voice_id}")
                tqdm.write(f"Phrase: '{phrase[:50]}{'...' if len(phrase) > 50 else ''}'")
                
                # Generate the audio
                start_time = time.time()
                audio_base64 = self.transcriber.text_to_speech_polly(
                    phrase, 
                    voice_id=voice_id,
                    output_format="mp3",
                    return_base64=True
                )
                duration = time.time() - start_time
                
                if audio_base64:
                    # Update the record in Supabase
                    self.supabase.table(self.table_name) \
                        .update({"phrase_audio": audio_base64, "updated_at": datetime.now().isoformat()}) \
                        .eq("id", card_id) \
                        .execute()
                    
                    success_count += 1
                    tqdm.write(f"✅ Updated card {card_id} with audio ({len(audio_base64)} chars, {duration:.2f}s)")
                else:
                    tqdm.write(f"❌ Failed to generate audio for card {card_id}")
                    failed_ids.append(card_id)
            
            except Exception as e:
                tqdm.write(f"Error processing card {card_id}: {e}")
                failed_ids.append(card_id)
        
        return success_count, failed_ids
    
    def update_word_audio(self, voice_id="Joanna"):
        """Update the word_audio field for flashcards that have the field empty.
        
        Args:
            voice_id (str): AWS Polly voice ID to use for all flashcards
            
        Returns:
            tuple: (success_count, failed_ids)
        """
        try:
            # Query for records where word_audio is null or empty but word is not empty
            response = (self.supabase.table(self.table_name)
                .select("id, word")
                .neq("word", None)
                .neq("word", "")
                .or_("word_audio.is.null,word_audio.eq.''")
                .execute())
            
            flashcards = response.data
            success_count = 0
            failed_ids = []
            
            print(f"Processing word audio for {len(flashcards)} flashcards...")
            
            # Use tqdm for progress bar
            for card in tqdm(flashcards, desc="Generating Word Audio"):
                card_id = card.get("id")
                word = card.get("word", "")
                
                try:
                    # Generate audio for just the word
                    audio_base64 = self.transcriber.text_to_speech_polly(
                        word, 
                        voice_id=voice_id,
                        output_format="mp3",
                        return_base64=True
                    )
                    
                    if audio_base64:
                        # Update the record
                        self.supabase.table(self.table_name) \
                            .update({"word_audio": audio_base64}) \
                            .eq("id", card_id) \
                            .execute()
                        
                        success_count += 1
                        tqdm.write(f"✅ Updated word audio for card {card_id}")
                    else:
                        tqdm.write(f"❌ Failed to generate word audio for card {card_id}")
                        failed_ids.append(card_id)
                
                except Exception as e:
                    tqdm.write(f"Error processing word audio for card {card_id}: {e}")
                    failed_ids.append(card_id)
            
            return success_count, failed_ids
        
        except Exception as e:
            print(f"Error updating word audio: {e}")
            return 0, []


def main():
    parser = argparse.ArgumentParser(description="Generate and update audio for flashcards in Supabase")
    parser.add_argument("--word-audio", action="store_true", help="Update word audio instead of phrase audio")
    parser.add_argument("--all", action="store_true", help="Update all flashcards, even those with existing audio")
    parser.add_argument("--voice", type=str, default="Joanna", help="AWS Polly voice ID to use (default: Joanna)")
    
    args = parser.parse_args()
    
    try:
        generator = FlashcardAudioGenerator()
        
        if args.word_audio:
            # Update word audio
            print("Updating word audio for all eligible flashcards...")
            success_count, failed_ids = generator.update_word_audio(voice_id=args.voice)
        else:
            # Get flashcards to process
            if args.all:
                print("Getting ALL flashcards for audio update...")
                flashcards = generator.get_all_flashcards()
            else:
                print("Getting flashcards WITHOUT audio...")
                flashcards = generator.get_flashcards_without_audio()
            
            if not flashcards:
                print("No flashcards found that match the criteria.")
                return
            
            # Generate audio and update the records
            success_count, failed_ids = generator.generate_audio_for_flashcards(flashcards, voice_id=args.voice)
        
        # Print summary
        print("\n--- Summary ---")
        print(f"Successfully updated {success_count} flashcards")
        if failed_ids:
            print(f"Failed to update {len(failed_ids)} flashcards with IDs: {failed_ids}")
        
    except Exception as e:
        print(f"Error in main function: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 