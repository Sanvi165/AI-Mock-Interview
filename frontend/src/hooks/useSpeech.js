import { useCallback, useEffect, useRef, useState } from "react";

const SpeechRecognitionAPI =
  typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : null;

const ERROR_MESSAGES = {
  "not-allowed": "Microphone permission was denied. Allow it in the browser address bar, or type your answer.",
  "service-not-allowed": "Speech recognition is not allowed in this browser. Please type your answer.",
  "no-speech": "No speech was detected. Try again or type your answer.",
  "audio-capture": "No microphone was found. Please type your answer.",
  network: "Speech recognition needs an internet connection in this browser. Please type your answer.",
};

/**
 * Browser speech features.
 * - Text-to-speech: speak(text) reads a question aloud.
 * - Speech-to-text: startListening() calls onFinalText(chunk) for each recognised phrase.
 * Both depend on browser support (speech recognition works in Chrome and Edge).
 */
export default function useSpeech({ onFinalText } = {}) {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState("");

  const recognitionRef = useRef(null);
  const callbackRef = useRef(onFinalText);

  useEffect(() => {
    callbackRef.current = onFinalText;
  }, [onFinalText]);

  const sttSupported = Boolean(SpeechRecognitionAPI);
  const ttsSupported = typeof window !== "undefined" && "speechSynthesis" in window;

  const startListening = useCallback(() => {
    if (!SpeechRecognitionAPI) {
      setError("Speech recognition is not supported in this browser. Please type your answer.");
      return;
    }
    setError("");
    const recognition = new SpeechRecognitionAPI();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let interimText = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) {
          const text = result[0].transcript.trim();
          if (text && callbackRef.current) callbackRef.current(text);
        } else {
          interimText += result[0].transcript;
        }
      }
      setInterim(interimText);
    };
    recognition.onerror = (event) => {
      setError(ERROR_MESSAGES[event.error] || "Speech recognition error. Please type your answer.");
      setListening(false);
    };
    recognition.onend = () => {
      setListening(false);
      setInterim("");
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
      setListening(true);
    } catch {
      setError("Could not start the microphone. Please type your answer.");
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) recognitionRef.current.stop();
  }, []);

  const stopSpeaking = useCallback(() => {
    if (ttsSupported) window.speechSynthesis.cancel();
    setSpeaking(false);
  }, [ttsSupported]);

  const speak = useCallback(
    (text) => {
      if (!ttsSupported || !text) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.onstart = () => setSpeaking(true);
      utterance.onend = () => setSpeaking(false);
      utterance.onerror = () => setSpeaking(false);
      window.speechSynthesis.speak(utterance);
    },
    [ttsSupported]
  );

  // Clean up when the page is closed.
  useEffect(
    () => () => {
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        recognitionRef.current.abort();
      }
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    },
    []
  );

  return {
    sttSupported,
    ttsSupported,
    listening,
    interim,
    speaking,
    error,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  };
}