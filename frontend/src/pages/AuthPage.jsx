import {
  ArrowRight,
  Camera,
  CheckCircle2,
  CloudSun,
  Eye,
  EyeOff,
  Leaf,
  LockKeyhole,
  MapPin,
  Mic,
  ShieldCheck,
  Sprout,
  UserRound,
} from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import ThemeToggle from "../components/ThemeToggle";
import { useAuth } from "../context/AuthContext";


const INITIAL_FORM = {
  email: "",
  password: "",
  full_name: "",
  language: "mr",
  state: "",
  district: "",
  village: "",
};


const HERO_FEATURES = [
  {
    icon: Sprout,
    title: "Crop guidance",
    description: "Practical help for everyday farming decisions.",
  },
  {
    icon: CloudSun,
    title: "Live weather",
    description: "Check weather before planning farm work.",
  },
  {
    icon: Camera,
    title: "Leaf analysis",
    description: "Share a crop image for visual guidance.",
  },
  {
    icon: Mic,
    title: "Voice questions",
    description: "Ask naturally in Marathi, Hindi or English.",
  },
];


export default function AuthPage() {
  const { signIn } = useAuth();

  const navigate = useNavigate();

  const emailRef =
    useRef(null);

  const passwordRef =
    useRef(null);

  const [mode, setMode] =
    useState("login");

  const [form, setForm] =
    useState(INITIAL_FORM);

  const [error, setError] =
    useState("");

  const [busy, setBusy] =
    useState(false);

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);


  const isLogin =
    mode === "login";


  /*
   * Always start with a completely empty form.
   *
   * This runs on page load and also resets the form
   * when the user switches between Login and Register.
   */
  useEffect(() => {
    setForm({
      ...INITIAL_FORM,
    });

    setError("");
    setShowPassword(false);

    /*
     * Some browsers attempt to restore login values from
     * autofill after React renders. Clearing the DOM values
     * once after mount keeps this entry screen clean.
     */
    const clearBrowserRestoredValues =
      () => {
        if (emailRef.current) {
          emailRef.current.value = "";
        }

        if (passwordRef.current) {
          passwordRef.current.value = "";
        }

        setForm((current) => ({
          ...current,
          email: "",
          password: "",
        }));
      };

    const frame =
      window.requestAnimationFrame(
        clearBrowserRestoredValues
      );

    const timeout =
      window.setTimeout(
        clearBrowserRestoredValues,
        120
      );

    return () => {
      window.cancelAnimationFrame(
        frame
      );

      window.clearTimeout(
        timeout
      );
    };
  }, [mode]);


  /*
   * Keep the authentication form clean if the user
   * comes back to /auth through browser navigation.
   */
  useEffect(() => {
    const handlePageShow =
      () => {
        setForm({
          ...INITIAL_FORM,
        });

        setError("");
        setShowPassword(false);
      };

    window.addEventListener(
      "pageshow",
      handlePageShow
    );

    return () =>
      window.removeEventListener(
        "pageshow",
        handlePageShow
      );
  }, []);


  const updateField = (
    key,
    value
  ) => {
    setForm(
      (current) => ({
        ...current,
        [key]: value,
      })
    );
  };


  const toggleMode = () => {
    setMode(
      (current) =>
        current === "login"
          ? "register"
          : "login"
    );
  };


  const submit =
    async (event) => {
      event.preventDefault();

      setError("");
      setBusy(true);

      try {
        const email =
          form.email.trim();

        const credentials =
          isLogin
            ? {
                email,
                password:
                  form.password,
              }
            : {
                email,
                password:
                  form.password,
                full_name:
                  form.full_name.trim(),
                language:
                  form.language,
                state:
                  form.state.trim(),
                district:
                  form.district.trim(),
                village:
                  form.village.trim(),
              };

        await signIn(
          credentials,
          mode
        );

        /*
         * Clear local form state immediately after
         * successful authentication.
         */
        setForm({
          ...INITIAL_FORM,
        });

        navigate(
          "/chat",
          {
            replace: true,
          }
        );
      } catch (err) {
        setError(
          err?.message ||
            "Unable to complete the request. Please try again."
        );
      } finally {
        setBusy(false);
      }
    };


  return (
    <main className="auth-page-pro">

      {/* ==================================================
          LEFT FIXED BRAND PANEL
          ================================================== */}

      <section className="auth-hero-pro">

        <div className="auth-hero-pattern" />

        <div className="auth-hero-circle circle-one" />
        <div className="auth-hero-circle circle-two" />
        <div className="auth-hero-circle circle-three" />


        <div className="auth-hero-content-pro">

          <div className="auth-brand-pro">
            <div className="auth-brand-icon-pro">
              <Leaf size={22} />
            </div>

            <div>
              <strong>
                KrishiSaathi
              </strong>

              <span>
                AI Farming Assistant
              </span>
            </div>
          </div>


          <div className="auth-hero-main-pro">

            <div className="auth-hero-eyebrow-pro">
              <span className="auth-live-dot" />

              BUILT FOR INDIAN FARMERS
            </div>


            <h1>
              Better farming
              decisions,
              <span>
                made simpler.
              </span>
            </h1>


            <p>
              Ask questions, understand your
              crops, check the weather, explore
              market information and get practical
              guidance in the language you prefer.
            </p>


            <div className="auth-feature-list-pro">
              {HERO_FEATURES.map(
                ({
                  icon: Icon,
                  title,
                  description,
                }) => (
                  <div
                    className="auth-feature-pro"
                    key={title}
                  >
                    <div className="auth-feature-icon-pro">
                      <Icon size={17} />
                    </div>

                    <div>
                      <strong>
                        {title}
                      </strong>

                      <span>
                        {description}
                      </span>
                    </div>
                  </div>
                )
              )}
            </div>

          </div>


          <div className="auth-hero-footer-pro">

            <div className="auth-security-pro">
              <ShieldCheck size={17} />

              <div>
                <strong>
                  Secure farmer workspace
                </strong>

                <span>
                  Your account and farm context stay protected.
                </span>
              </div>
            </div>

          </div>

        </div>

      </section>


      {/* ==================================================
          RIGHT SCROLLABLE PANEL
          ================================================== */}

      <section className="auth-form-panel-pro">

        <header className="auth-panel-top-pro">

          <div className="auth-mobile-brand-pro">
            <div className="auth-mobile-icon-pro">
              <Leaf size={18} />
            </div>

            <div>
              <strong>
                KrishiSaathi
              </strong>

              <span>
                AI Farming Assistant
              </span>
            </div>
          </div>


          <ThemeToggle />

        </header>


        <div className="auth-panel-scroll-pro">

          <div className="auth-card-pro">

            {/* TOP LABEL */}

            <div className="auth-card-label-row-pro">

              <span className="auth-card-label-pro">
                {isLogin
                  ? "FARMER WORKSPACE"
                  : "QUICK SETUP"}
              </span>


              <span className="auth-secure-label-pro">
                <span className="auth-secure-dot-pro" />

                SECURE
              </span>

            </div>


            {/* HEADING */}

            <div className="auth-card-heading-pro">

              <div className="auth-card-heading-icon-pro">
                {isLogin ? (
                  <LockKeyhole size={18} />
                ) : (
                  <UserRound size={18} />
                )}
              </div>


              <div>
                <h2>
                  {isLogin
                    ? "Welcome back"
                    : "Create your account"}
                </h2>

                <p>
                  {isLogin
                    ? "Continue your farming workspace and conversations."
                    : "Set up your farmer profile for more useful guidance."}
                </p>
              </div>

            </div>


            {/* ERROR */}

            {error && (
              <div
                className="auth-error-pro"
                role="alert"
              >
                <span>
                  {error}
                </span>
              </div>
            )}


            {/* FORM */}

            <form
              className="auth-form-pro"
              onSubmit={
                submit
              }
              autoComplete="off"
            >

              {mode === "register" && (
                <>

                  <label className="auth-field-pro">
                    <span>
                      Full name
                    </span>

                    <div className="auth-control-pro">
                      <UserRound size={16} />

                      <input
                        type="text"
                        value={
                          form.full_name
                        }
                        onChange={(
                          event
                        ) =>
                          updateField(
                            "full_name",
                            event.target.value
                          )
                        }
                        placeholder="Your full name"
                        autoComplete="off"
                        autoCapitalize="words"
                        required
                      />
                    </div>
                  </label>


                  <div className="auth-grid-two-pro">

                    <label className="auth-field-pro">
                      <span>
                        State
                      </span>

                      <div className="auth-control-pro">
                        <MapPin size={16} />

                        <input
                          type="text"
                          value={
                            form.state
                          }
                          onChange={(
                            event
                          ) =>
                            updateField(
                              "state",
                              event.target.value
                            )
                          }
                          placeholder="Maharashtra"
                          autoComplete="off"
                        />
                      </div>
                    </label>


                    <label className="auth-field-pro">
                      <span>
                        District
                      </span>

                      <div className="auth-control-pro">
                        <MapPin size={16} />

                        <input
                          type="text"
                          value={
                            form.district
                          }
                          onChange={(
                            event
                          ) =>
                            updateField(
                              "district",
                              event.target.value
                            )
                          }
                          placeholder="Nagpur"
                          autoComplete="off"
                        />
                      </div>
                    </label>

                  </div>


                  <label className="auth-field-pro">
                    <span>
                      Village / town
                    </span>

                    <div className="auth-control-pro">
                      <MapPin size={16} />

                      <input
                        type="text"
                        value={
                          form.village
                        }
                        onChange={(
                          event
                        ) =>
                          updateField(
                            "village",
                            event.target.value
                          )
                        }
                        placeholder="Village or town"
                        autoComplete="off"
                      />
                    </div>
                  </label>


                  <label className="auth-field-pro">
                    <span>
                      Preferred language
                    </span>

                    <div className="auth-control-pro">
                      <Leaf size={16} />

                      <select
                        value={
                          form.language
                        }
                        onChange={(
                          event
                        ) =>
                          updateField(
                            "language",
                            event.target.value
                          )
                        }
                      >
                        <option value="mr">
                          Marathi
                        </option>

                        <option value="hi">
                          Hindi
                        </option>

                        <option value="en">
                          English
                        </option>
                      </select>
                    </div>
                  </label>

                </>
              )}


              <label className="auth-field-pro">
                <span>
                  Email address
                </span>

                <div className="auth-control-pro">

                  <input
                    ref={
                      emailRef
                    }
                    type="email"
                    name="krishi-email"
                    value={
                      form.email
                    }
                    onChange={(
                      event
                    ) =>
                      updateField(
                        "email",
                        event.target.value
                      )
                    }
                    placeholder="you@example.com"
                    autoComplete="off"
                    autoCorrect="off"
                    spellCheck="false"
                    inputMode="email"
                    required
                  />

                </div>
              </label>


              <label className="auth-field-pro">
                <span>
                  Password
                </span>

                <div className="auth-control-pro password-control-pro">

                  <input
                    ref={
                      passwordRef
                    }
                    type={
                      showPassword
                        ? "text"
                        : "password"
                    }
                    name="krishi-password"
                    value={
                      form.password
                    }
                    onChange={(
                      event
                    ) =>
                      updateField(
                        "password",
                        event.target.value
                      )
                    }
                    placeholder="Enter your password"
                    autoComplete="new-password"
                    required
                    minLength={8}
                  />


                  <button
                    type="button"
                    className="password-toggle-pro"
                    onClick={() =>
                      setShowPassword(
                        (
                          value
                        ) =>
                          !value
                      )
                    }
                    aria-label={
                      showPassword
                        ? "Hide password"
                        : "Show password"
                    }
                    tabIndex={0}
                  >
                    {showPassword ? (
                      <EyeOff
                        size={17}
                      />
                    ) : (
                      <Eye
                        size={17}
                      />
                    )}
                  </button>

                </div>
              </label>


              <button
                type="submit"
                className="auth-submit-pro"
                disabled={busy}
              >
                <span>
                  {busy
                    ? isLogin
                      ? "Signing in..."
                      : "Creating account..."
                    : isLogin
                      ? "Sign in"
                      : "Create account"}
                </span>

                {!busy && (
                  <ArrowRight
                    size={18}
                  />
                )}
              </button>

            </form>


            {/* SECURITY INFO */}

            <div className="auth-note-pro">

              <CheckCircle2
                size={15}
              />

              <span>
                {isLogin
                  ? "Your farming workspace is ready when you are."
                  : "Your account details help personalize your farming assistant."}
              </span>

            </div>


            {/* SWITCH LOGIN / REGISTER */}

            <div className="auth-switch-pro">

              <span>
                {isLogin
                  ? "New to KrishiSaathi?"
                  : "Already have an account?"}
              </span>

              <button
                type="button"
                onClick={
                  toggleMode
                }
              >
                {isLogin
                  ? "Create account"
                  : "Sign in"}
              </button>

            </div>

          </div>

          <div className="auth-bottom-copy-pro">
            AI-powered farming support for everyday decisions.
          </div>

        </div>

      </section>

    </main>
  );
}