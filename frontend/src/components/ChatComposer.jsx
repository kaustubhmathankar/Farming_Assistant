import {
  ImagePlus,
  Languages,
  Mic,
  Send,
  Square,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

const VOICE_LANGUAGES = [
  { value: "auto", label: "Auto" },
  { value: "mr", label: "मराठी" },
  { value: "hi", label: "हिन्दी" },
  { value: "en", label: "English" },
];

const MAX_IMAGE_SIZE_MB = 10;

export default function ChatComposer({
  value,
  onChange,
  onSend,
  image,
  setImage,
  recording,
  onToggleRecording,
  disabled,
  voiceLanguage = "auto",
  onVoiceLanguageChange,
  recordingSeconds = 0,
}) {
  const [preview, setPreview] = useState("");
  const textareaRef = useRef(null);

  useEffect(() => {
    if (!image) {
      setPreview("");
      return undefined;
    }

    const url = URL.createObjectURL(image);
    setPreview(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [image]);

  useEffect(() => {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    textarea.style.height = "auto";

    const maxHeight =
      window.innerWidth <= 560
        ? 110
        : 140;

    textarea.style.height = `${Math.min(
      textarea.scrollHeight,
      maxHeight
    )}px`;
  }, [value]);

  const handleImageChange = (event) => {
    const file =
      event.target.files?.[0] || null;

    event.target.value = "";

    if (!file) {
      return;
    }

    if (!file.type.startsWith("image/")) {
      window.alert(
        "Please select a valid crop image."
      );
      return;
    }

    if (
      file.size >
      MAX_IMAGE_SIZE_MB * 1024 * 1024
    ) {
      window.alert(
        `Image must be smaller than ${MAX_IMAGE_SIZE_MB} MB.`
      );
      return;
    }

    setImage(file);
  };

  const submit = (event) => {
    event?.preventDefault();

    if (
      !disabled &&
      (value.trim() || image)
    ) {
      onSend();
    }
  };

  return (
    <div className="composer-wrap">
      {image && (
        <div className="attachment-preview">
          <div className="attachment-thumb-wrap">
            <img
              src={preview}
              alt="Selected crop"
              className="attachment-thumb"
            />
          </div>

          <div className="attachment-copy">
            <strong>
              Crop image attached
            </strong>

            <span>
              {image.name}
            </span>

            <small>
              Ask a question with the image
              or send it alone.
            </small>
          </div>

          <button
            type="button"
            className="attachment-remove"
            onClick={() =>
              setImage(null)
            }
            aria-label="Remove attached crop image"
            title="Remove image"
            disabled={disabled}
          >
            <X size={17} />
          </button>
        </div>
      )}

      <form
        className="composer"
        onSubmit={submit}
      >
        <label
          className="composer-icon"
          title="Upload crop image"
          aria-label="Upload crop image"
        >
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleImageChange}
            hidden
            disabled={disabled}
          />

          <ImagePlus size={20} />
        </label>

        <div className="composer-editor">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) =>
              onChange(event.target.value)
            }
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey
              ) {
                event.preventDefault();
                submit(event);
              }
            }}
            placeholder={
              image
                ? "Ask something about this crop image…"
                : "Ask about your crop, soil, weather, market price…"
            }
            rows={1}
            disabled={disabled}
            aria-label="Ask your farming question"
          />

          <div className="composer-editor-footer">
            <span className="composer-status">
              {image
                ? "Image ready"
                : "KrishiSaathi is ready"}
            </span>

            <span className="composer-key-hint">
              Enter to send · Shift + Enter for a new line
            </span>
          </div>
        </div>

        <div className="voice-controls">
          <div
            className="voice-language-control"
            title="Choose the language you will speak"
          >
            <Languages size={14} />

            <select
              value={voiceLanguage}
              onChange={(event) =>
                onVoiceLanguageChange?.(
                  event.target.value
                )
              }
              disabled={
                disabled || recording
              }
              aria-label="Voice input language"
            >
              {VOICE_LANGUAGES.map(
                (item) => (
                  <option
                    key={item.value}
                    value={item.value}
                  >
                    {item.label}
                  </option>
                )
              )}
            </select>
          </div>

          {recording && (
            <span
              className="recording-timer"
              aria-live="polite"
            >
              {recordingSeconds}s
            </span>
          )}

          <button
            className={`voice-btn ${
              recording
                ? "recording"
                : ""
            }`}
            type="button"
            onClick={
              onToggleRecording
            }
            aria-label={
              recording
                ? "Stop recording"
                : "Start voice recording"
            }
            title={
              recording
                ? "Stop recording"
                : "Voice input"
            }
            disabled={disabled}
          >
            {recording ? (
              <Square size={17} />
            ) : (
              <Mic size={19} />
            )}
          </button>
        </div>

        <button
          className="send-btn"
          type="submit"
          disabled={
            disabled ||
            (!value.trim() && !image)
          }
          aria-label="Send message"
          title="Send message"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}