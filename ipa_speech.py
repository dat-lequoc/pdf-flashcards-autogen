#!/usr/bin/env python3
"""
Alternative test script for IPA transcription and text-to-speech.
This script uses eng_to_ipa for English IPA transcription and AWS Polly for audio.
"""

import os
import sys
import argparse
import base64
from datetime import datetime
import eng_to_ipa
import time
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class IPATranscriber:
    """Class for handling IPA transcription and text-to-speech operations."""
    
    def __init__(self):
        """Initialize the IPATranscriber."""
        # Initialize AWS Polly client
        self.polly_client = boto3.client(
            'polly', 
            region_name='us-east-1',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )
    
    def get_ipa(self, word):
        """Convert English text to IPA transcription.
        
        Args:
            word (str): Text to transcribe
            
        Returns:
            str: IPA transcription or None if error
        """
        try:
            # Get IPA transcription
            ipa = eng_to_ipa.convert(word)
            return ipa
        except Exception as e:
            print(f"Error with eng_to_ipa: {e}")
            return None
    
    def text_to_speech_polly(self, text, voice_id='Joanna', output_format='mp3', 
                            save_path=None, return_base64=False):
        """Generate speech using AWS Polly.
        
        Args:
            text (str): Text to synthesize
            voice_id (str): AWS Polly voice ID
            output_format (str): Audio format (mp3, ogg_vorbis, pcm)
            save_path (str, optional): Path to save audio file
            return_base64 (bool): If True, return base64 encoded audio instead of saving to file
            
        Returns:
            str: Path to saved audio file or base64 encoded audio string
        """
        try:
            # If no save path is provided and we're not returning base64, create a path
            if save_path is None and not return_base64:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                save_path = f"test_audio_{timestamp}.{output_format}"
            
            start_time = time.time()
            
            # Request speech synthesis
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat=output_format,
                VoiceId=voice_id
            )
            
            duration = time.time() - start_time
            
            # Handle the audio data based on the return_base64 flag
            if "AudioStream" in response:
                audio_data = response['AudioStream'].read()
                
                if return_base64:
                    # Convert audio data to base64 string
                    base64_audio = base64.b64encode(audio_data).decode('utf-8')
                    return base64_audio
                else:
                    # Save audio to file
                    with open(save_path, 'wb') as file:
                        file.write(audio_data)
                    return save_path
            else:
                print("No AudioStream found in the response")
                return None
                
        except (BotoCoreError, ClientError) as error:
            print(f"Error with AWS Polly: {error}")
            return None
        except Exception as e:
            print(f"Unexpected error with AWS Polly: {e}")
            return None
    
    def text_to_speech_gtts(self, text, lang='en', save_path=None, return_base64=False):
        """Generate speech using gTTS.
        
        Args:
            text (str): Text to synthesize
            lang (str): Language code
            save_path (str, optional): Path to save audio file
            return_base64 (bool): If True, return base64 encoded audio instead of saving to file
            
        Returns:
            str: Path to saved audio file or base64 encoded audio string
        """
        try:
            # Import gTTS here to make it optional
            from gtts import gTTS
            import io
            
            # If no save path is provided and we're not returning base64, create one
            if save_path is None and not return_base64:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                save_path = f"test_audio_{timestamp}.mp3"
            
            # Create TTS audio
            start_time = time.time()
            tts = gTTS(text, lang=lang)
            
            if return_base64:
                # Save to BytesIO object instead of file
                mp3_fp = io.BytesIO()
                tts.write_to_fp(mp3_fp)
                mp3_fp.seek(0)
                
                # Convert to base64
                base64_audio = base64.b64encode(mp3_fp.read()).decode('utf-8')
                return base64_audio
            else:
                # Save to file
                tts.save(save_path)
                return save_path
                
        except Exception as e:
            print(f"Error with gTTS: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="Test IPA transcription and text-to-speech")
    parser.add_argument("--word", "-w", type=str, help="Word to transcribe/speak")
    parser.add_argument("--words-file", "-f", type=str, help="File containing words to transcribe (one per line)")
    parser.add_argument("--words-list", "-l", type=str, help="Comma-separated list of words to transcribe")
    parser.add_argument("--ipa-only", action="store_true", help="Only perform IPA transcription, skip TTS")
    parser.add_argument("--tts-service", type=str, default="polly", choices=["gtts", "polly"], 
                        help="TTS service to use (gtts or polly)")
    parser.add_argument("--tts-lang", type=str, default="en", help="gTTS language code")
    parser.add_argument("--voice-id", type=str, default="Joanna", 
                        help="AWS Polly voice ID (e.g., Joanna, Matthew)")
    parser.add_argument("--output-format", type=str, default="mp3", choices=["mp3", "ogg_vorbis", "pcm"],
                        help="AWS Polly output format")
    parser.add_argument("--output", "-o", type=str, help="Output path for audio file")
    parser.add_argument("--base64", action="store_true", 
                        help="Return base64 encoded audio string instead of saving to file")
    
    args = parser.parse_args()
    
    # Get words to process
    words = []
    
    if args.word:
        words.append(args.word)
    
    if args.words_list:
        words.extend([w.strip() for w in args.words_list.split(',')])
    
    if args.words_file:
        try:
            with open(args.words_file, 'r') as f:
                words.extend([line.strip() for line in f if line.strip()])
        except Exception as e:
            print(f"Error reading words file: {e}")
    
    if not words:
        print("Please provide words using --word, --words-list, or --words-file")
        return
    
    # Create transcriber instance
    transcriber = IPATranscriber()
    
    # Process each word
    results = []
    print("\n--- IPA Transcription Results ---")
    print("-" * 40)
    print(f"{'Word':<20} | {'IPA Transcription'}")
    print("-" * 40)
    
    for word in words:
        ipa = transcriber.get_ipa(word)
        results.append((word, ipa))
        print(f"{word:<20} | {ipa if ipa else 'Failed to transcribe'}")
    
    # Skip TTS if ipa-only flag is set
    if args.ipa_only:
        return
    
    # Continue with TTS for the first word or as needed
    # Test TTS based on selected service
    result = None
    if args.tts_service == "gtts":
        print(f"\n--- Testing gTTS for: '{words[0]}' in {args.tts_lang} ---")
        print(f"Generating audio...")
        start_time = time.time()
        result = transcriber.text_to_speech_gtts(words[0], args.tts_lang, args.output, args.base64)
        duration = time.time() - start_time
        result_type = "Base64 audio" if args.base64 else "Audio file"
        if result:
            if args.base64:
                print(f"Generated base64 audio string ({len(result)} characters)")
            else:
                print(f"Audio saved to: {os.path.abspath(result)}")
            print(f"Generation time: {duration:.2f} seconds")
    else:  # default to polly
        print(f"\n--- Testing AWS Polly for: '{words[0]}' with voice {args.voice_id} ---")
        print(f"Generating audio...")
        start_time = time.time()
        result = transcriber.text_to_speech_polly(
            words[0], args.voice_id, args.output_format, args.output, args.base64
        )
        duration = time.time() - start_time
        result_type = "Base64 audio" if args.base64 else "Audio file"
        if result:
            if args.base64:
                print(f"Generated base64 audio string ({len(result)} characters)")
            else:
                print(f"Audio saved to: {os.path.abspath(result)}")
            print(f"Generation time: {duration:.2f} seconds")
    
    if results[0][1] and result:
        print(f"\n✅ Both tests completed successfully!")
        print(f"Word: {results[0][0]}")
        print(f"IPA:  {results[0][1]}")
        if args.base64:
            print(f"{result_type}: [base64 string - {len(result)} characters]")
        else:
            print(f"{result_type}: {os.path.abspath(result)}")
    else:
        print("\n❌ Some tests failed. See above for details.")

if __name__ == "__main__":
    main() 