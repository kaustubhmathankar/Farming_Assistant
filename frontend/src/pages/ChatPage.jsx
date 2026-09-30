import {
  MapPin,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import ChatComposer from "../components/ChatComposer";
import MessageBubble from "../components/MessageBubble";
import { api } from "../services/api";


const starterPrompts = [
  "माझ्या कापसाच्या पिकासाठी आज काय काळजी घ्यावी?",
  "What should I do if my crop leaves are turning yellow?",
  "आज नागपूरमधील हवामान शेतीसाठी कसे आहे?",
  "Find current mandi prices for cotton in Maharashtra.",
];


function createFreshState() {
  return {
    messages: [],
    error: "",
    input: "",
    image: null,
  };
}


function createLocalId(prefix) {
  if (
    globalThis.crypto?.randomUUID
  ) {
    return `${prefix}-${globalThis.crypto.randomUUID()}`;
  }

  return `${prefix}-${Date.now()}-${Math.random()
    .toString(36)
    .slice(2)}`;
}


/*
 * Make sure the user's message is painted before
 * the thinking indicator is shown.
 */
function waitForMessagePaint() {
  return new Promise(
    (resolve) => {
      window.requestAnimationFrame(
        () => {
          window.requestAnimationFrame(
            () => resolve()
          );
        }
      );
    }
  );
}


export default function ChatPage() {
  const {
    user,
    refreshUser,
  } = useAuth();

  const locationState =
    useLocation();

  const navigate =
    useNavigate();


  const [messages, setMessages] =
    useState([]);

  const [input, setInput] =
    useState("");

  const [image, setImage] =
    useState(null);

  const [
    conversationId,
    setConversationId,
  ] = useState(
    () =>
      localStorage.getItem(
        "krishisaathi_conversation"
      ) || ""
  );

  const [busy, setBusy] =
    useState(false);

  const [
    recording,
    setRecording,
  ] = useState(false);

  const [
    recordingSeconds,
    setRecordingSeconds,
  ] = useState(0);

  const [
    voiceLanguage,
    setVoiceLanguage,
  ] = useState(
    () =>
      localStorage.getItem(
        "krishisaathi_voice_language_v2"
      ) || "auto"
  );

  const [
    loadingConversation,
    setLoadingConversation,
  ] = useState(false);

  const [error, setError] =
    useState("");


  const mediaRecorder =
    useRef(null);

  const chunks =
    useRef([]);

  const bottom =
    useRef(null);

  const recordingTimer =
    useRef(null);

  /*
   * Contains both locally-created image URLs
   * and URLs created after restoring images
   * from the backend.
   */
  const localImageUrls =
    useRef(new Set());


  const language =
    user?.farmer?.language ||
    "mr";


  const farmLocation = [
    user?.farmer?.village,
    user?.farmer?.district,
    user?.farmer?.state,
  ]
    .filter(Boolean)
    .join(", ");


  const greeting =
    useMemo(
      () =>
        user?.farmer?.full_name
          ? `Hello ${
              user.farmer.full_name.split(
                " "
              )[0]
            } 👋`
          : "Hello, farmer 👋",
      [user]
    );


  const queryConversationId =
    useMemo(() => {
      const params =
        new URLSearchParams(
          locationState.search
        );

      return (
        params.get(
          "conversation"
        ) || ""
      );
    }, [locationState.search]);


  const isNewChatRequest =
    useMemo(() => {
      const params =
        new URLSearchParams(
          locationState.search
        );

      return (
        params.get(
          "new"
        ) === "1"
      );
    }, [locationState.search]);


  const revokeLocalImageUrls =
    useCallback(() => {
      localImageUrls.current.forEach(
        (url) => {
          try {
            URL.revokeObjectURL(
              url
            );
          } catch {
            // Ignore already released URLs.
          }
        }
      );

      localImageUrls.current.clear();
    }, []);


  /*
   * Restore persisted images when loading
   * an existing conversation.
   */
  const hydrateConversationMessages =
    useCallback(
      async (
        rawMessages
      ) => {
        const safeMessages =
          Array.isArray(
            rawMessages
          )
            ? rawMessages
            : [];

        const hydrated =
          await Promise.all(
            safeMessages.map(
              async (
                message
              ) => {
                if (
                  !message?.image_url
                ) {
                  return message;
                }

                try {
                  const objectUrl =
                    await api.imageBlobUrl(
                      message.image_url
                    );

                  localImageUrls.current.add(
                    objectUrl
                  );

                  return {
                    ...message,
                    image_preview_url:
                      objectUrl,
                  };
                } catch (
                  imageError
                ) {
                  console.warn(
                    "[CHAT] Could not restore image:",
                    imageError
                  );

                  return message;
                }
              }
            )
          );

        return hydrated;
      },
      []
    );


  useEffect(() => {
    const handleProfileUpdated =
      async () => {
        try {
          await refreshUser();
        } catch {
          // Backend is still the source of truth.
        }
      };

    window.addEventListener(
      "krishisaathi:profile-updated",
      handleProfileUpdated
    );

    return () =>
      window.removeEventListener(
        "krishisaathi:profile-updated",
        handleProfileUpdated
      );
  }, [refreshUser]);


  useEffect(() => {
    let cancelled = false;


    async function loadConversation() {
      revokeLocalImageUrls();


      if (
        isNewChatRequest
      ) {
        const fresh =
          createFreshState();

        setConversationId("");
        setMessages(
          fresh.messages
        );
        setError(
          fresh.error
        );
        setInput(
          fresh.input
        );
        setImage(
          fresh.image
        );

        localStorage.removeItem(
          "krishisaathi_conversation"
        );

        return;
      }


      const targetId =
        queryConversationId ||
        localStorage.getItem(
          "krishisaathi_conversation"
        ) ||
        "";


      if (!targetId) {
        setConversationId("");
        setMessages([]);

        return;
      }


      setLoadingConversation(
        true
      );

      setError("");


      try {
        const data =
          await api.conversation(
            targetId
          );


        if (
          cancelled
        ) {
          return;
        }


        const hydratedMessages =
          await hydrateConversationMessages(
            data.messages || []
          );


        if (
          cancelled
        ) {
          revokeLocalImageUrls();
          return;
        }


        setConversationId(
          data.id
        );

        setMessages(
          hydratedMessages
        );


        localStorage.setItem(
          "krishisaathi_conversation",
          data.id
        );
      } catch (
        requestError
      ) {
        if (
          cancelled
        ) {
          return;
        }


        if (
          requestError?.status ===
          404
        ) {
          localStorage.removeItem(
            "krishisaathi_conversation"
          );

          setConversationId("");
          setMessages([]);

          navigate(
            "/chat?new=1",
            {
              replace: true,
            }
          );
        } else {
          setError(
            requestError?.message ||
              "Unable to load this conversation."
          );
        }
      } finally {
        if (
          !cancelled
        ) {
          setLoadingConversation(
            false
          );
        }
      }
    }


    loadConversation();


    return () => {
      cancelled = true;
    };
  }, [
    hydrateConversationMessages,
    isNewChatRequest,
    navigate,
    queryConversationId,
    revokeLocalImageUrls,
  ]);


  useEffect(() => {
    bottom.current?.scrollIntoView(
      {
        behavior: "smooth",
        block: "end",
      }
    );
  }, [
    messages,
    busy,
  ]);


  useEffect(() => {
    const onKeyDown =
      (event) => {
        if (
          (event.ctrlKey ||
            event.metaKey) &&
          event.key.toLowerCase() ===
            "k"
        ) {
          event.preventDefault();

          navigate(
            "/chat?new=1"
          );
        }
      };

    window.addEventListener(
      "keydown",
      onKeyDown
    );

    return () =>
      window.removeEventListener(
        "keydown",
        onKeyDown
      );
  }, [navigate]);


  const persistConversation =
    (id) => {
      if (!id) {
        return;
      }

      setConversationId(
        id
      );

      localStorage.setItem(
        "krishisaathi_conversation",
        id
      );

      navigate(
        `/chat?conversation=${encodeURIComponent(
          id
        )}`,
        {
          replace: true,
        }
      );

      window.dispatchEvent(
        new CustomEvent(
          "krishisaathi:conversations-updated"
        )
      );
    };


  const appendUserMessage =
    (
      content,
      inputType = "text",
      attachmentFile = null
    ) => {
      const id =
        createLocalId("u");

      let imagePreviewUrl =
        "";


      if (
        attachmentFile instanceof File
      ) {
        imagePreviewUrl =
          URL.createObjectURL(
            attachmentFile
          );

        localImageUrls.current.add(
          imagePreviewUrl
        );
      }


      setMessages(
        (
          current
        ) => [
          ...current,
          {
            id,
            role: "user",
            content,
            input_type:
              inputType,
            language,
            image_preview_url:
              imagePreviewUrl,
            image_name:
              attachmentFile?.name ||
              "",
          },
        ]
      );

      return id;
    };


  const appendAssistantMessage =
    (data) => {
      setMessages(
        (
          current
        ) => [
          ...current,
          {
            id:
              createLocalId(
                "a"
              ),
            role: "assistant",
            content:
              data.answer,
            sources:
              data.sources || [],
            language:
              data.language ||
              language,
          },
        ]
      );

      persistConversation(
        data.conversation_id
      );
    };


  const sendText =
    async () => {
      const text =
        input.trim();


      if (
        (!text && !image) ||
        busy
      ) {
        return;
      }


      const outgoingText =
        text ||
        "Please check this crop image.";


      const outgoingImage =
        image;


      setError("");


      /*
       * Immediately show:
       *   image + question
       * before backend processing starts.
       */
      appendUserMessage(
        outgoingText,
        outgoingImage
          ? "image"
          : "text",
        outgoingImage
      );


      setInput("");
      setImage(null);


      /*
       * Allow browser to paint the message.
       */
      await waitForMessagePaint();


      setBusy(true);


      try {
        if (
          outgoingImage
        ) {
          const form =
            new FormData();


          form.append(
            "question",
            outgoingText
          );


          if (
            conversationId
          ) {
            form.append(
              "conversation_id",
              conversationId
            );
          }


          form.append(
            "image",
            outgoingImage
          );


          const data =
            await api.imageChat(
              form
            );


          appendAssistantMessage(
            data
          );
        } else {
          const data =
            await api.chat({
              message:
                outgoingText,
              conversation_id:
                conversationId ||
                null,
              language,
              location:
                farmLocation,
            });


          appendAssistantMessage(
            data
          );
        }
      } catch (
        requestError
      ) {
        console.error(
          "[CHAT] Request error:",
          requestError
        );

        setError(
          requestError?.message ||
            "Unable to process your question right now."
        );
      } finally {
        setBusy(false);
      }
    };


  useEffect(() => {
    localStorage.setItem(
      "krishisaathi_voice_language_v2",
      voiceLanguage
    );
  }, [
    voiceLanguage,
  ]);


  useEffect(() => {
    return () => {
      window.clearInterval(
        recordingTimer.current
      );

      try {
        if (
          mediaRecorder.current
            ?.state ===
          "recording"
        ) {
          mediaRecorder.current.stop();
        }
      } catch {
        // Recorder already stopped.
      }


      revokeLocalImageUrls();
    };
  }, [
    revokeLocalImageUrls,
  ]);


  const startRecording =
    async () => {
      if (
        !navigator.mediaDevices
          ?.getUserMedia ||
        busy
      ) {
        setError(
          "Microphone recording is not available in this browser."
        );

        return;
      }


      try {
        const stream =
          await navigator.mediaDevices.getUserMedia(
            {
              audio: {
                channelCount: 1,
                echoCancellation:
                  true,
                noiseSuppression:
                  true,
                autoGainControl:
                  true,
              },
            }
          );


        const mimeType =
          [
            "audio/webm;codecs=opus",
            "audio/webm",
            "audio/mp4",
          ].find(
            (type) =>
              MediaRecorder.isTypeSupported?.(
                type
              )
          );


        if (
          !mimeType
        ) {
          stream
            .getTracks()
            .forEach(
              (
                track
              ) =>
                track.stop()
            );

          throw new Error(
            "No supported audio recording format is available."
          );
        }


        const recorder =
          new MediaRecorder(
            stream,
            {
              mimeType,
            }
          );


        chunks.current =
          [];


        setRecordingSeconds(
          0
        );


        recorder.ondataavailable =
          (event) => {
            if (
              event.data?.size
            ) {
              chunks.current.push(
                event.data
              );
            }
          };


        recorder.onstop =
          async () => {
            stream
              .getTracks()
              .forEach(
                (
                  track
                ) =>
                  track.stop()
              );


            const audio =
              new Blob(
                chunks.current,
                {
                  type: mimeType,
                }
              );


            chunks.current =
              [];


            if (
              !audio.size
            ) {
              setError(
                "No audio was recorded. Please try again."
              );

              return;
            }


            const form =
              new FormData();


            if (
              conversationId
            ) {
              form.append(
                "conversation_id",
                conversationId
              );
            }


            form.append(
              "voice_language",
              voiceLanguage
            );


            form.append(
              "audio",
              audio,
              mimeType.includes(
                "mp4"
              )
                ? "voice.m4a"
                : "voice.webm"
            );


            setBusy(true);
            setError("");


            try {
              const data =
                await api.voiceChat(
                  form
                );


              const answerLanguage =
                data.language ||
                language;


              appendUserMessage(
                data.transcript,
                "voice"
              );


              appendAssistantMessage(
                data
              );


              setInput("");


              speak(
                data.answer,
                answerLanguage
              );
            } catch (
              requestError
            ) {
              console.error(
                "[VOICE] Request error:",
                requestError
              );

              setError(
                requestError?.message ||
                  "Unable to process your voice message."
              );
            } finally {
              setBusy(false);
            }
          };


        recorder.start(250);


        mediaRecorder.current =
          recorder;


        setRecording(
          true
        );


        recordingTimer.current =
          window.setInterval(
            () => {
              setRecordingSeconds(
                (
                  current
                ) => {
                  const next =
                    current + 1;


                  if (
                    next >= 20
                  ) {
                    window.clearInterval(
                      recordingTimer.current
                    );


                    try {
                      if (
                        mediaRecorder.current
                          ?.state ===
                        "recording"
                      ) {
                        mediaRecorder.current.stop();
                      }
                    } catch {
                      // Recorder already stopped.
                    }
                  }


                  return Math.min(
                    next,
                    20
                  );
                }
              );
            },
            1000
          );
      } catch (
        requestError
      ) {
        console.error(
          "[VOICE] Microphone error:",
          requestError
        );


        setError(
          requestError?.message ||
            "Microphone permission was denied or the microphone is unavailable."
        );


        setRecording(
          false
        );
      }
    };


  const stopRecording =
    () => {
      window.clearInterval(
        recordingTimer.current
      );


      setRecording(
        false
      );


      setRecordingSeconds(
        0
      );


      const recorder =
        mediaRecorder.current;


      mediaRecorder.current =
        null;


      if (
        recorder?.state ===
        "recording"
      ) {
        recorder.stop();
      }
    };


  const toggleRecording =
    () => {
      if (
        recording
      ) {
        stopRecording();
      } else {
        startRecording();
      }
    };


  const speak =
    (
      text,
      code = language
    ) => {
      if (
        !window.speechSynthesis
      ) {
        return;
      }


      window.speechSynthesis.cancel();


      const utterance =
        new SpeechSynthesisUtterance(
          text || ""
        );


      utterance.lang =
        {
          en: "en-IN",
          hi: "hi-IN",
          mr: "mr-IN",
        }[code] ||
        "mr-IN";


      window.speechSynthesis.speak(
        utterance
      );
    };


  const showWelcome =
    !messages.length &&
    !loadingConversation;


  return (
    <section className="chat-page">
      <div className="chat-header">
        <div>
          <div className="eyebrow">
            <Sparkles size={14} />
            Farming copilot
          </div>

          <h1>
            Your farm, your questions.
          </h1>

          <p>
            Talk, type, or share a crop
            photo. KrishiSaathi brings
            your profile and trusted
            agriculture sources together.
          </p>
        </div>
      </div>


      {farmLocation && (
        <div className="context-strip">
          <MapPin size={15} />

          <span>
            Using your farm context:
          </span>

          <strong>
            {farmLocation}
          </strong>
        </div>
      )}


      {error && (
        <div className="alert error">
          {error}
        </div>
      )}


      {loadingConversation ? (
        <div className="chat-loading-state">
          <div className="loading-spinner">
            <RefreshCw size={19} />
          </div>

          <strong>
            Opening your conversation…
          </strong>

          <span>
            Your previous farming messages
            are loading.
          </span>
        </div>
      ) : showWelcome ? (
        <div className="chat-canvas welcome-canvas">
          <div className="welcome">
            <div className="welcome-orb">
              <Sparkles size={26} />
            </div>

            <p className="welcome-kicker">
              {greeting}
            </p>

            <h2>
              What can we solve on your farm today?
            </h2>

            <p className="welcome-copy">
              Ask about crop health, soil,
              weather, mandi prices,
              government schemes, or anything
              you want help understanding.
            </p>

            <div className="prompt-grid">
              {starterPrompts.map(
                (
                  prompt
                ) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() =>
                      setInput(
                        prompt
                      )
                    }
                    className="prompt-card"
                  >
                    <span>
                      {prompt}
                    </span>

                    <span
                      aria-hidden="true"
                    >
                      ↗
                    </span>
                  </button>
                )
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="chat-canvas has-messages">
          <div className="message-list">
            {messages.map(
              (
                message
              ) => (
                <MessageBubble
                  key={
                    message.id
                  }
                  message={
                    message
                  }
                  languageCode={
                    language
                  }
                />
              )
            )}


            {busy && (
              <div className="thinking-row">
                <div className="message-role-label">
                  <div className="avatar message-avatar">
                    <Sparkles size={16} />
                  </div>

                  <span>
                    KrishiSaathi
                  </span>
                </div>

                <div className="thinking-bubble">
                  <span className="thinking-dot" />

                  <span>
                    Checking the right information…
                  </span>
                </div>
              </div>
            )}


            <div ref={bottom} />
          </div>
        </div>
      )}


      <ChatComposer
        value={
          input
        }
        onChange={
          setInput
        }
        onSend={
          sendText
        }
        image={
          image
        }
        setImage={
          setImage
        }
        recording={
          recording
        }
        onToggleRecording={
          toggleRecording
        }
        disabled={
          busy
        }
        voiceLanguage={
          voiceLanguage
        }
        onVoiceLanguageChange={
          setVoiceLanguage
        }
        recordingSeconds={
          recordingSeconds
        }
      />
    </section>
  );
}