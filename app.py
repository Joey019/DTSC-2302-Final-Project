import streamlit as st
from urllib.parse import quote_plus

st.set_page_config(
    page_title="Plotwist | Find Your Next Read",
    page_icon="📖",
    layout="wide"
)


# Initialize the user's reading list
if "reading_list" not in st.session_state:
    st.session_state.reading_list = []
    

# Display notifications after page refreshes
if "notification" in st.session_state:
    st.toast(st.session_state.pop("notification"))




st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

:root {
    --background: #0D1520;
    --surface: #192838;
    --surface-hover: #24384C;
    --accent: #F2B86D;
    --text: #FFF4E6;
    --muted: #AEBAC7;
}

.stApp {
    background:
        radial-gradient(ellipse at 85% 5%, #283B4C 0%, transparent 40%),
        var(--background);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    max-width: 1250px;
    padding-top: 2.5rem;
    padding-bottom: 5rem;
}

h1, h2, h3 {
    font-family: 'Outfit', sans-serif !important;
    color: var(--text) !important;
    letter-spacing: -0.04em;
}

h1 {
    font-size: clamp(2.8rem, 5vw, 4.5rem) !important;
    font-weight: 800 !important;
}

h2 {
    font-weight: 700 !important;
}

p {
    line-height: 1.65;
}

.stButton > button {
    background: var(--accent);
    color: #142232;
    border: none;
    border-radius: 12px;
    font-weight: 700;
    padding: 0.7rem 1.5rem;
    transition: transform 0.2s, background 0.2s;
}

.stButton > button:hover {
    background: #FFD39A;
    color: #142232;
    border: none;
    transform: translateY(-2px);
}

div[data-baseweb="select"] > div {
    background: var(--surface);
    border: 1px solid #425468;
    border-radius: 12px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface);
    border: 1px solid #30465A;
    border-radius: 18px;
    transition: border-color 0.2s, transform 0.2s;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--accent);
    transform: translateY(-3px);
}

div[data-testid="stImage"] img {
    border-radius: 10px;
}

hr {
    border-color: #30465A;
}

@media (prefers-reduced-motion: reduce) {
    * {
        transition: none !important;
        animation: none !important;
    }
}


/* Consistent book cover appearance */
div[data-testid="stImage"] img {
    aspect-ratio: 2 / 3;
    object-fit: cover;
    border-radius: 10px;
    transition: transform 0.25s ease,
                box-shadow 0.25s ease;
}

/* Subtle book cover hover effect */
div[data-testid="stImage"] img:hover {
    transform: scale(1.025);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

/* Smoother button interactions */
.stButton button {
    transition: transform 0.2s ease,
                background-color 0.2s ease,
                box-shadow 0.2s ease;
}

.stButton button:active {
    transform: scale(0.97);
}

/* Smooth expandable sections */
div[data-testid="stExpander"] {
    border-radius: 10px;
    transition: border-color 0.2s ease;
}


/* Plotwist footer */
.plotwist-footer {
    margin-top: 80px;
    padding: 40px 20px 25px;
    text-align: center;
    border-top: 1px solid rgba(242, 184, 109, 0.2);
}

.footer-logo {
    font-family: 'Outfit', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: #F2B86D;
    margin-bottom: 8px;
}

.footer-tagline {
    color: #AEBAC7;
    font-size: 14px;
    margin-bottom: 30px;
}

.footer-divider {
    width: 45px;
    height: 2px;
    background: #F2B86D;
    margin: 0 auto 25px;
}

.footer-bottom {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    color: #8899AA;
    font-size: 12px;
}

@media (max-width: 600px) {
    .footer-bottom {
        flex-direction: column;
        align-items: center;
    }
}



</style>
""", unsafe_allow_html=True)


# Website branding
st.markdown(
    "<h2 style='color:#F2B86D; margin-bottom:0;'>"
    "📖 plotwist.</h2>",
    unsafe_allow_html=True
)

st.caption("THE ART OF THE UNEXPECTED")

st.divider()

# Cinematic hero section
left, right = st.columns([1.4, 1], gap="large")

with left:
    st.markdown(
        "<p style='color:#F2B86D; font-weight:700;"
        "letter-spacing:3px;'>"
        "MYSTERY · THRILLER · CRIME</p>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<h1>Your next favorite book is "
        "<span style='color:#F2B86D;'>"
        "hiding in plain sight.</span></h1>",
        unsafe_allow_html=True
    )

    st.write(
        "The stories that keep you guessing. "
        "The endings you never saw coming. "
        "Discover your next obsession with Plotwist."
    )

    st.markdown("**Explore stories that stay with you.**")

with right:
    st.image(
        "https://images.unsplash.com/photo-1507842217343-583bb7270b66"
        "?auto=format&fit=crop&w=900&q=85",
        width="stretch"
    )

st.markdown(
    "<p style='color:#F2B86D; letter-spacing:2px;'>"
    "PSYCHOLOGICAL THRILLERS &nbsp; · &nbsp; "
    "MURDER MYSTERIES &nbsp; · &nbsp; "
    "CRIME FICTION</p>",
    unsafe_allow_html=True
)

# Featured Thrillers section
st.markdown("## Featured Thrillers")
st.caption("Handpicked stories for your next reading obsession.")

featured_books = [
    ("The Silent Patient", "Alex Michaelides", "Psychological Thriller", "9781250301697"),
    ("Gone Girl", "Gillian Flynn", "Mystery Thriller", "9780307588371"),
    ("The Guest List", "Lucy Foley", "Crime Mystery", "9780062868930"),
    ("Sharp Objects", "Gillian Flynn", "Psychological Mystery", "9780307341556"),
    ("The Girl on the Train", "Paula Hawkins", "Suspense Thriller", "9781594634024")
]

featured_columns = st.columns(5, gap="medium")

for i, (title, author, genre, isbn) in enumerate(featured_books):
    with featured_columns[i]:
        with st.container(border=True):
            st.image(
                f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg",
                width="stretch"
            )
            st.markdown(f"**{title}**")
            st.caption(author)
            st.caption(genre)
            
            if st.button(
                "Explore Book",
                key=f"featured_{i}",
                use_container_width=True
            ):
                st.session_state.selected_book = title
                st.rerun()


st.divider()

st.divider()
st.markdown("### Find your next obsession")
st.caption(
    "Choose a book you loved and discover similar stories."
)


# Temporary book list until we connect the Goodreads dataset
books = [
    "Gone Girl",
    "The Silent Patient",
    "The Guest List",
    "The Girl on the Train",
    "The Woman in the Window",
    "Big Little Lies",
    "The Da Vinci Code",
    "The Shining",
    "Sharp Objects",
    "The Couple Next Door"
]

book = st.selectbox(
    "What book did you love?",
    options=books,
    index=None,
    placeholder="Search for a book you enjoyed..."
)


# Temporary recommendations for testing the UI
recommendations = {
    "Gone Girl": [
        ("The Girl on the Train", "Paula Hawkins"),
        ("The Silent Patient", "Alex Michaelides"),
        ("Sharp Objects", "Gillian Flynn"),
        ("The Woman in the Window", "A.J. Finn"),
        ("The Couple Next Door", "Shari Lapena")
    ],
    "The Silent Patient": [
        ("Gone Girl", "Gillian Flynn"),
        ("The Woman in the Window", "A.J. Finn"),
        ("The Girl on the Train", "Paula Hawkins"),
        ("Sharp Objects", "Gillian Flynn"),
        ("The Guest List", "Lucy Foley")
    ]
}

#Book Covers
book_covers = {
    "Gone Girl": "https://covers.openlibrary.org/b/isbn/9780307588371-L.jpg",
    "The Girl on the Train": "https://covers.openlibrary.org/b/isbn/9781594634024-L.jpg",
    "The Silent Patient": "https://covers.openlibrary.org/b/isbn/9781250301697-L.jpg",
    "Sharp Objects": "https://covers.openlibrary.org/b/isbn/9780307341556-L.jpg",
    "The Woman in the Window": "https://covers.openlibrary.org/b/isbn/9780062678416-L.jpg",
    "The Couple Next Door": "https://covers.openlibrary.org/b/isbn/9780735221109-L.jpg",
    "The Guest List": "https://covers.openlibrary.org/b/isbn/9780062868930-L.jpg"
}

if st.button("Find my next read"):
    if book:
        with st.spinner("Finding your next plot twist...", show_time=True):
            # Temporary selection logic
            # The recommendation model will go here later
            st.session_state.selected_book = book
    else:
        st.warning("Please select a book first.")

        

# Welcome state before the first recommendation
if "selected_book" not in st.session_state:
    st.markdown("### ✨ Your next plot twist starts here")
    st.caption(
        "Choose a book you already love, then click "
        "'Find my next read' to discover similar "
        "mysteries, thrillers, and unforgettable stories."
    )

    st.info(
        "📖 Not sure where to start? Try Gone Girl "
        "or The Silent Patient."
    )



if "selected_book" in st.session_state:
    selected = st.session_state.selected_book

    st.divider()
    st.markdown(f"## Because you liked *{selected}*")
    st.caption("Preview recommendations — AI model not connected yet.")

    results = recommendations.get(
        selected,
        [
            ("Gone Girl", "Gillian Flynn"),
            ("The Silent Patient", "Alex Michaelides"),
            ("The Guest List", "Lucy Foley"),
            ("Sharp Objects", "Gillian Flynn"),
            ("The Girl on the Train", "Paula Hawkins")
        ]
    )

    columns = st.columns(5, gap="medium")

    for i, (title, author) in enumerate(results):
        with columns[i]:
            with st.container(border=True):
                cover = book_covers.get(title)

                if cover:
                    st.image(cover, width="stretch")
                else:
                    st.markdown("📖")

                st.markdown(f"**{title}**")
                st.caption(author)
                
                
                book_key = (title, author)

                if book_key in st.session_state.reading_list:
                    st.caption("♥ Saved to reading list")
                else:
                    if st.button(
                        "♡ Save for Later",
                        key=f"save_{i}_{title}",
                        use_container_width=True
                    ):
                        
                        st.session_state.reading_list.append(book_key)
                        st.session_state.notification = (
                            f"📚 {title} added to your reading list!"
                        )
                        st.rerun()



                with st.expander("View details"):
                    st.write(f"**Title:** {title}")
                    st.write(f"**Author:** {author}")
                    st.caption(
                        "Full book descriptions coming soon."
                    )
                
                # Automatically generate shopping links
                search = quote_plus(f"{title} {author}")

                with st.expander("🛒 Where to Buy"):
                    st.link_button(
                        "Amazon",
                        f"https://www.amazon.com/s?k={search}&i=stripbooks",
                        use_container_width=True
                    )

                    st.link_button(
                        "Barnes & Noble",
                        f"https://www.barnesandnoble.com/s/{search}",
                        use_container_width=True
                    )

                    st.link_button(
                        "Bookshop.org",
                        f"https://bookshop.org/search?keywords={search}",
                        use_container_width=True
                    )

                    st.caption(
                        "Check the retailer for current prices "
                        "and available editions."
                    )
    


# Personal reading list section
st.divider()

st.markdown("## ♡ Your Reading List")
st.caption("Your personal collection of books to read next.")

if st.session_state.reading_list:

    st.markdown(
        f"**{len(st.session_state.reading_list)} books saved**"
    )

    saved_books = st.session_state.reading_list.copy()

    columns = st.columns(4, gap="medium")

    for i, (title, author) in enumerate(saved_books):

        with columns[i % 4]:
            with st.container(border=True):

                # Display cover if available
                cover = book_covers.get(title)

                if cover:
                    st.image(cover, width="stretch")
                else:
                    st.markdown("📖")

                st.markdown(f"**{title}**")
                st.caption(author)

                if st.button(
                    "Remove",
                    key=f"remove_saved_{i}",
                    use_container_width=True
                ):
                    
                    st.session_state.reading_list.remove(
                        (title, author)
                    )
                    st.session_state.notification = (
                        f"Removed {title} from your reading list."
                    )
                    st.rerun()


else:
    st.info(
        "Your reading list is empty. "
        "Explore recommendations and save books you love!"
    )


# ---------------------------------------
# PLOTWIST FOOTER
# ---------------------------------------

st.markdown(
    """
    <div class="plotwist-footer">
        <div class="footer-logo">📖 plotwist.</div>
        <div class="footer-tagline">
            Every great story starts with a twist.
        </div>
        <div class="footer-divider"></div>
        <div class="footer-bottom">
            <span>Made for readers who love the unexpected.</span>
            <span>UNC Charlotte | DTSC 2302</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
