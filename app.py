import streamlit as st

st.set_page_config(
    page_title="Plotwist | Find Your Next Read",
    page_icon="📖",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #111D2A;
    color: #F7F1E7;
}
h1, h2, h3 {
    color: #F7F1E7 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("📖 plotwist.")
st.caption("FOR THE PLOT OBSESSED")

st.markdown("## Your next obsession is one plot twist away.")
st.write("Tell us what you couldn't put down. We'll find your next late-night read.")

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
        st.session_state.selected_book = book
    else:
        st.warning("Please select a book first.")
        



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

    columns = st.columns(5)

    for i, (title, author) in enumerate(results):
        with columns[i]:
            cover = book_covers.get(title)

            if cover:
                st.image(cover, width="stretch")
            else:
                st.markdown("📖")

            st.markdown(f"**{title}**")
            st.caption(author)