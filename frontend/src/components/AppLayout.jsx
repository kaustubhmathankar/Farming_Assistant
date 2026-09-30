import {
  Bot,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Home,
  LogOut,
  MapPin,
  Menu,
  MessageSquarePlus,
  MessageSquareText,
  Shield,
  Trash2,
  UserRound,
  X,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";

import ThemeToggle from "./ThemeToggle";

import {
  useAuth,
} from "../context/AuthContext";

import {
  api,
} from "../services/api";


const SIDEBAR_COLLAPSED_KEY =
  "krishisaathi_sidebar_collapsed";


function formatConversationDate(
  value
) {
  if (!value) {
    return "";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return "";
  }

  const now =
    new Date();

  const sameDay =
    date.getFullYear() ===
      now.getFullYear() &&
    date.getMonth() ===
      now.getMonth() &&
    date.getDate() ===
      now.getDate();

  if (sameDay) {
    return date.toLocaleTimeString(
      [],
      {
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  }

  const diff =
    Math.floor(
      (
        new Date(
          now.getFullYear(),
          now.getMonth(),
          now.getDate()
        ) -
        new Date(
          date.getFullYear(),
          date.getMonth(),
          date.getDate()
        )
      ) /
        86400000
    );

  if (diff === 1) {
    return "Yesterday";
  }

  if (
    diff >= 0 &&
    diff < 7
  ) {
    return date.toLocaleDateString(
      [],
      {
        weekday: "short",
      }
    );
  }

  return date.toLocaleDateString(
    [],
    {
      day: "2-digit",
      month: "short",
    }
  );
}


function groupConversations(
  items
) {
  const groups = [];

  const today =
    new Date();

  const startToday =
    new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate()
    );

  const startWeek =
    new Date(
      startToday
    );

  startWeek.setDate(
    startWeek.getDate() -
      7
  );

  const buckets = [
    {
      label: "Today",

      test: (
        date
      ) =>
        date >=
        startToday,
    },

    {
      label:
        "Previous 7 days",

      test: (
        date
      ) =>
        date >=
          startWeek &&
        date <
          startToday,
    },

    {
      label: "Older",

      test: (
        date
      ) =>
        date <
        startWeek,
    },
  ];

  for (
    const bucket of buckets
  ) {
    const matches =
      items.filter(
        (
          item
        ) => {
          const date =
            new Date(
              item.updated_at ||
                item.created_at
            );

          return (
            !Number.isNaN(
              date.getTime()
            ) &&
            bucket.test(
              date
            )
          );
        }
      );

    if (
      matches.length
    ) {
      groups.push({
        label:
          bucket.label,

        items:
          matches,
      });
    }
  }

  return groups;
}


export default function AppLayout() {
  const {
    user,
    isAdmin,
    signOut,
  } = useAuth();

  const location =
    useLocation();

  const navigate =
    useNavigate();


  const [
    mobileOpen,
    setMobileOpen,
  ] = useState(false);


  const [
    collapsed,
    setCollapsed,
  ] = useState(
    () =>
      localStorage.getItem(
        SIDEBAR_COLLAPSED_KEY
      ) === "true"
  );


  const [
    conversations,
    setConversations,
  ] = useState([]);


  const [
    historyLoading,
    setHistoryLoading,
  ] = useState(true);


  const [
    accountMenuOpen,
    setAccountMenuOpen,
  ] = useState(false);


  const [
    signingOut,
    setSigningOut,
  ] = useState(false);


  const accountMenuRef =
    useRef(null);


  /*
   * Active conversation ID from URL.
   */
  const activeConversationId =
    useMemo(() => {
      const params =
        new URLSearchParams(
          location.search
        );

      return (
        params.get(
          "conversation"
        ) || ""
      );
    }, [
      location.search,
    ]);


  /*
   * Farm location shown in the navbar
   * and sidebar.
   */
  const farmLocation =
    useMemo(() => {
      return [
        user?.farmer?.district,
        user?.farmer?.state,
      ]
        .filter(Boolean)
        .join(", ");
    }, [
      user,
    ]);


  /*
   * Load conversation history.
   */
  const loadConversations =
    useCallback(
      async () => {
        try {
          setHistoryLoading(
            true
          );

          const data =
            await api.conversations();

          setConversations(
            Array.isArray(
              data?.items
            )
              ? data.items
              : []
          );
        } catch (
          error
        ) {
          /*
           * Do not force logout here.
           *
           * A conversation-history failure should
           * not accidentally log the farmer out.
           */
          if (
            error?.status !==
            401
          ) {
            console.error(
              "[SIDEBAR] Conversation history error:",
              error
            );
          }
        } finally {
          setHistoryLoading(
            false
          );
        }
      },
      []
    );


  /*
   * Load conversations when layout mounts
   * and when ChatPage announces an update.
   */
  useEffect(() => {
    loadConversations();

    const refresh =
      () =>
        loadConversations();

    window.addEventListener(
      "krishisaathi:conversations-updated",
      refresh
    );

    return () =>
      window.removeEventListener(
        "krishisaathi:conversations-updated",
        refresh
      );
  }, [
    loadConversations,
  ]);


  /*
   * Close mobile/sidebar account menus
   * whenever the route changes.
   */
  useEffect(() => {
    setMobileOpen(
      false
    );

    setAccountMenuOpen(
      false
    );
  }, [
    location.pathname,
  ]);


  /*
   * Close account dropdown when clicking
   * outside it or pressing Escape.
   */
  useEffect(() => {
    const onPointerDown =
      (
        event
      ) => {
        if (
          !accountMenuRef.current?.contains(
            event.target
          )
        ) {
          setAccountMenuOpen(
            false
          );
        }
      };


    const onKeyDown =
      (
        event
      ) => {
        if (
          event.key ===
          "Escape"
        ) {
          setAccountMenuOpen(
            false
          );
        }
      };


    document.addEventListener(
      "mousedown",
      onPointerDown
    );

    document.addEventListener(
      "keydown",
      onKeyDown
    );


    return () => {
      document.removeEventListener(
        "mousedown",
        onPointerDown
      );

      document.removeEventListener(
        "keydown",
        onKeyDown
      );
    };
  }, []);


  /*
   * Collapse / expand sidebar.
   */
  const toggleCollapsed =
    () => {
      setCollapsed(
        (
          value
        ) => {
          const next =
            !value;

          localStorage.setItem(
            SIDEBAR_COLLAPSED_KEY,
            String(next)
          );

          return next;
        }
      );
    };


  /*
   * Start a completely new chat.
   */
  const newChat =
    () => {
      navigate(
        "/chat?new=1"
      );

      setMobileOpen(
        false
      );
    };


  /*
   * Open an existing conversation.
   */
  const openConversation =
    (
      id
    ) => {
      navigate(
        `/chat?conversation=${encodeURIComponent(
          id
        )}`
      );

      setMobileOpen(
        false
      );
    };


  /*
   * Open farmer profile.
   */
  const openProfile =
    () => {
      setAccountMenuOpen(
        false
      );

      navigate(
        "/profile"
      );
    };


  /*
   * Explicit logout.
   *
   * There is no logout action attached to
   * the email/profile button.
   */
  const handleSignOut =
    async () => {
      if (
        signingOut
      ) {
        return;
      }

      setSigningOut(
        true
      );

      setAccountMenuOpen(
        false
      );

      try {
        await signOut();
      } catch (
        error
      ) {
        console.error(
          "[AUTH] Sign out error:",
          error
        );
      } finally {
        navigate(
          "/auth",
          {
            replace: true,
          }
        );

        setSigningOut(
          false
        );
      }
    };


  /*
   * Delete one conversation.
   */
  const removeConversation =
    async (
      conversation
    ) => {
      const title =
        conversation.title ||
        "this conversation";


      const confirmed =
        window.confirm(
          `Delete “${title}”?`
        );


      if (
        !confirmed
      ) {
        return;
      }


      try {
        await api.deleteConversation(
          conversation.id
        );


        window.dispatchEvent(
          new CustomEvent(
            "krishisaathi:conversations-updated"
          )
        );


        if (
          activeConversationId ===
          conversation.id
        ) {
          navigate(
            "/chat?new=1"
          );
        }

      } catch (
        error
      ) {
        console.error(
          "[SIDEBAR] Delete conversation error:",
          error
        );
      }
    };


  /*
   * Current page title.
   */
  const pageTitle =
    location.pathname ===
    "/chat"
      ? "Farming Assistant"
      : location.pathname ===
          "/profile"
        ? "My Farm Profile"
        : location.pathname ===
            "/admin"
          ? "Admin Console"
          : "KrishiSaathi";


  /*
   * Group conversations by date.
   */
  const groups =
    useMemo(
      () =>
        groupConversations(
          conversations
        ),
      [
        conversations,
      ]
    );


  /*
   * Main navigation.
   */
  const nav = [
    {
      to: "/chat",
      label:
        "Farming Assistant",
      icon:
        MessageSquareText,
    },

    {
      to: "/profile",
      label:
        "My Farm Profile",
      icon:
        UserRound,
    },
  ];


  /*
   * Admin-only navigation.
   */
  if (
    isAdmin
  ) {
    nav.push({
      to: "/admin",
      label:
        "Admin Console",
      icon:
        Shield,
    });
  }


  return (
    <div
      className={`app-shell ${
        collapsed
          ? "sidebar-collapsed"
          : ""
      }`}
    >

      {/* ====================================================
          SIDEBAR
          ==================================================== */}

      <aside
        className={`sidebar ${
          mobileOpen
            ? "open"
            : ""
        }`}
      >

        {/* ---------------- Brand ---------------- */}

        <div className="sidebar-brand-row">

          <div className="brand">

            <div className="brand-mark">
              <Bot size={20} />
            </div>


            {!collapsed && (
              <div>
                <strong>
                  KrishiSaathi
                </strong>

                <span>
                  AI Farming Assistant
                </span>
              </div>
            )}

          </div>


          <button
            className="mobile-close"
            onClick={() =>
              setMobileOpen(
                false
              )
            }
            aria-label="Close navigation"
            type="button"
          >
            <X size={18} />
          </button>

        </div>


        {/* ---------------- Sidebar content ---------------- */}

        <div className="sidebar-scroll">

          {/* New chat */}

          <button
            className="new-chat-btn"
            type="button"
            onClick={
              newChat
            }
            title={
              collapsed
                ? "New chat"
                : undefined
            }
          >

            <MessageSquarePlus
              size={18}
            />


            {!collapsed && (
              <span>
                New chat
              </span>
            )}


            {!collapsed && (
              <kbd>
                Ctrl K
              </kbd>
            )}

          </button>


          {/* Navigation label */}

          <div className="sidebar-section-label">

            {!collapsed && (
              <span>
                Navigation
              </span>
            )}

          </div>


          {/* Main navigation */}

          <nav
            className="primary-nav"
            aria-label="Primary navigation"
          >

            {nav.map(
              ({
                to,
                label,
                icon: Icon,
              }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({
                    isActive,
                  }) =>
                    `nav-item ${
                      isActive
                        ? "active"
                        : ""
                    }`
                  }
                  title={
                    collapsed
                      ? label
                      : undefined
                  }
                  onClick={() =>
                    setMobileOpen(
                      false
                    )
                  }
                >

                  <Icon size={18} />

                  {!collapsed && (
                    <span>
                      {label}
                    </span>
                  )}

                </NavLink>
              )
            )}

          </nav>


          {/* Recent conversations */}

          <div className="history-header">

            {!collapsed && (
              <>
                <div>
                  <span>
                    Recent conversations
                  </span>

                  <small>
                    Saved to your account
                  </small>
                </div>

                <Clock3 size={15} />
              </>
            )}

          </div>


          {!collapsed && (
            <div className="conversation-history">

              {/* Loading */}

              {historyLoading ? (

                <div className="history-state">

                  <span className="history-skeleton" />

                  <span className="history-skeleton short" />

                  <span className="history-skeleton" />

                </div>

              ) : groups.length ? (

                groups.map(
                  (
                    group
                  ) => (
                    <div
                      className="conversation-group"
                      key={
                        group.label
                      }
                    >

                      <div className="conversation-group-label">
                        {
                          group.label
                        }
                      </div>


                      {group.items.map(
                        (
                          conversation
                        ) => (
                          <div
                            className={`conversation-item ${
                              activeConversationId ===
                              conversation.id
                                ? "active"
                                : ""
                            }`}
                            key={
                              conversation.id
                            }
                          >

                            <button
                              type="button"
                              className="conversation-main"
                              onClick={() =>
                                openConversation(
                                  conversation.id
                                )
                              }
                            >

                              <MessageSquareText
                                size={15}
                              />


                              <span className="conversation-copy">

                                <strong>
                                  {
                                    conversation.title ||
                                    "New farming chat"
                                  }
                                </strong>


                                <small>
                                  {formatConversationDate(
                                    conversation.updated_at ||
                                      conversation.created_at
                                  )}
                                </small>

                              </span>

                            </button>


                            <button
                              type="button"
                              className="conversation-delete"
                              onClick={() =>
                                removeConversation(
                                  conversation
                                )
                              }
                              aria-label={`Delete ${
                                conversation.title ||
                                "conversation"
                              }`}
                              title="Delete conversation"
                            >
                              <Trash2
                                size={14}
                              />
                            </button>

                          </div>
                        )
                      )}

                    </div>
                  )
                )

              ) : (

                /* Empty */

                <div className="history-empty">

                  <MessageSquarePlus
                    size={18}
                  />

                  <strong>
                    No conversations yet
                  </strong>

                  <span>
                    Start a new farming chat.
                  </span>

                </div>

              )}

            </div>
          )}

        </div>


        {/* =================================================
            SIDEBAR BOTTOM
            ================================================= */}

        <div className="sidebar-bottom">

          {!collapsed && (
            <div className="location-chip">

              <span className="status-dot" />

              <span>
                {
                  user?.farmer?.district ||
                  user?.farmer?.state ||
                  "Your farm"
                }
              </span>

            </div>
          )}


          {/* Account */}

          <div className="account-row">

            <button
              type="button"
              className="account-profile-trigger"
              onClick={
                openProfile
              }
              title="Open my farm profile"
            >

              <span className="account-avatar">
                <UserRound size={16} />
              </span>


              {!collapsed && (
                <span className="account-copy">

                  <strong>
                    {
                      user?.farmer?.full_name ||
                      "Farmer"
                    }
                  </strong>


                  <span>
                    {
                      user?.email ||
                      ""
                    }
                  </span>

                </span>
              )}

            </button>


            {!collapsed && (
              <div
                className="account-menu-wrap"
                ref={
                  accountMenuRef
                }
              >

                <button
                  type="button"
                  className="account-more"
                  onClick={() =>
                    setAccountMenuOpen(
                      (
                        value
                      ) =>
                        !value
                    )
                  }
                  title="Account options"
                  aria-label="Open account options"
                  aria-expanded={
                    accountMenuOpen
                  }
                >

                  <span className="account-more-dots">
                    •••
                  </span>

                </button>


                {accountMenuOpen && (
                  <div
                    className="account-menu"
                    role="menu"
                  >

                    <button
                      type="button"
                      onClick={
                        openProfile
                      }
                      role="menuitem"
                    >
                      <UserRound
                        size={15}
                      />

                      Profile
                    </button>

                  </div>
                )}

              </div>
            )}

          </div>


          {/* Collapse */}

          <button
            type="button"
            className="collapse-btn"
            onClick={
              toggleCollapsed
            }
            title={
              collapsed
                ? "Expand sidebar"
                : "Collapse sidebar"
            }
          >

            {collapsed ? (
              <ChevronRight
                size={16}
              />
            ) : (
              <ChevronLeft
                size={16}
              />
            )}


            {!collapsed && (
              <span>
                Collapse
              </span>
            )}

          </button>

        </div>

      </aside>


      {/* ====================================================
          MOBILE BACKDROP
          ==================================================== */}

      <div
        className={`mobile-backdrop ${
          mobileOpen
            ? "show"
            : ""
        }`}
        onClick={() =>
          setMobileOpen(
            false
          )
        }
        aria-hidden="true"
      />


      {/* ====================================================
          MAIN
          ==================================================== */}

      <main className="main-panel">

        {/* ==================================================
            PROFESSIONAL TOP NAVBAR
            ================================================== */}

        <header className="topbar topbar-pro">

          {/* LEFT */}

          <div className="topbar-left-pro">

            <button
              className="mobile-menu"
              onClick={() =>
                setMobileOpen(
                  true
                )
              }
              aria-label="Open navigation"
              type="button"
            >
              <Menu size={20} />
            </button>


            <div
              className="breadcrumbs-pro"
              aria-label="Breadcrumb"
            >

              <span className="breadcrumb-home-pro">
                <Home size={15} />
              </span>


              <span className="breadcrumb-divider-pro">
                /
              </span>


              <span className="breadcrumb-page-pro">
                {
                  pageTitle
                }
              </span>

            </div>

          </div>


          {/* RIGHT */}

          <div className="topbar-right-pro">

            {/* AI STATUS */}

            <div
              className="topbar-status-pro"
              title="KrishiSaathi AI is ready"
            >

              <span className="topbar-status-dot-pro" />

              <span>
                AI ready
              </span>

            </div>


            {/* FARM LOCATION */}

            {farmLocation ? (
              <div
                className="topbar-farm-pro"
                title={`Farm location: ${farmLocation}`}
              >

                <MapPin
                  size={13}
                />

                <span>
                  {
                    farmLocation
                  }
                </span>

              </div>
            ) : null}


            {/* PROFILE */}

            <button
              type="button"
              className="topbar-profile-pro"
              onClick={
                openProfile
              }
              title="Open my farm profile"
            >

              <span className="topbar-avatar-pro">
                <UserRound
                  size={15}
                />
              </span>


              <span className="topbar-profile-copy-pro">

                <strong>
                  {
                    user?.farmer?.full_name ||
                    "Farmer"
                  }
                </strong>


                <small>
                  {
                    user?.email ||
                    ""
                  }
                </small>

              </span>

            </button>


            {/* THEME */}

            <div className="topbar-theme-pro">
              <ThemeToggle />
            </div>


            {/* SEPARATE LOGOUT */}

            <button
              type="button"
              className="topbar-logout-pro"
              onClick={
                handleSignOut
              }
              disabled={
                signingOut
              }
              title="Sign out of KrishiSaathi"
              aria-label="Sign out of KrishiSaathi"
            >

              <LogOut
                size={16}
              />

              <span>
                {
                  signingOut
                    ? "Signing out..."
                    : "Sign out"
                }
              </span>

            </button>

          </div>

        </header>


        {/* ==================================================
            PAGE CONTENT
            ================================================== */}

        <Outlet />

      </main>

    </div>
  );
}