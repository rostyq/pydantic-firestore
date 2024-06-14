from pytest import fixture, mark

from google.cloud.firestore import DocumentReference, CollectionReference, Client

from pydantic_firestore.reference import FirestoreDocument, FirestoreCollection


@fixture
def client() -> Client:
    return Client()


DOC_EXAMPLES = [
    ("col", "0"),
    ("col", "0", "sub_col", "00"),
]

COL_EXAMPLES = [
    ("col",),
    ("col", "0", "sub_col"),
]


@mark.parametrize("path", DOC_EXAMPLES)
def test_from_document(path: tuple[str, ...]):
    doc_ref = DocumentReference(*path)
    fs_doc = FirestoreDocument.from_firestore(doc_ref)

    assert fs_doc.model_dump() == path


@mark.parametrize("path", DOC_EXAMPLES)
def test_to_document(path: tuple[str, ...], client: Client):
    fs_doc = FirestoreDocument(root=path)

    assert fs_doc.to_firestore(client)._path == path


@mark.parametrize("path", COL_EXAMPLES)
def test_from_collection(path: tuple[str, ...]):
    col_ref = CollectionReference(*path)
    fs_col = FirestoreCollection.from_firestore(col_ref)

    assert fs_col.model_dump() == path


@mark.parametrize("path", COL_EXAMPLES)
def test_to_collection(path: tuple[str, ...], client: Client):
    fs_col = FirestoreCollection(root=path)

    assert fs_col.to_firestore(client)._path == path


@mark.xfail
@mark.parametrize("path", COL_EXAMPLES)
def test_document_from_col_path(path: tuple[str, ...]):
    FirestoreDocument(root=path)


@mark.xfail
@mark.parametrize("path", DOC_EXAMPLES)
def test_collection_from_doc_path(path: tuple[str, ...]):
    FirestoreCollection(root=path)
