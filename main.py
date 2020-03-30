import pickle
from copy import copy

import scholarly
import os

from scholarly import Publication, Author

path_to_authors = "./data/authors/"
path_to_publications = "./data/publications/"
pending_citations_file = "pending_citations.pkl"
limit_citations = 100


class ExtendedPublication(Publication):

    def __init__(self, pub):
        self.author = None
        self.cited_in = list()
        if isinstance(pub, Publication):
            self.bib = pub.bib
            self.source = pub.source
            if pub.source == 'citations':
                self.id_citations = pub.id_citations
            self.citedby = pub.citedby
            if hasattr(pub, 'id_scholarcitedby'):
                self.id_scholarcitedby = pub.id_scholarcitedby
            if hasattr(pub, 'url_scholarbib'):
                self.url_scholarbib = pub.url_scholarbib
            self.filled = pub._filled

    def fill_author(self):
        author_query = scholarly.search_author(self.bib['author'])
        self.author = next(author_query).fill()


def save_author(author: Author):
    """
    Save author to local file (pickle)
    :param author:
    :return:
    """
    if author is not None and hasattr(author, 'id'):
        # remove publications to save. can be recovery by using .fill()
        author.publications = None

        local_filename = os.path.join(path_to_authors, '{}.pkl'.format(author.id))
        os.makedirs(os.path.dirname(local_filename), exist_ok=True)
        if not os.path.isfile(local_filename):
            with open(local_filename, 'wb') as f:
                pickle.dump(author, f, pickle.HIGHEST_PROTOCOL)


def save_publication(publication: Publication):
    """
    Save publication to local file (pickle)
    :param publication: publication object
    :return:
    """
    if publication is not None and hasattr(publication, 'id_scholarcitedby'):
        local_filename = os.path.join(path_to_publications, '{}.pkl'.format(publication.id_scholarcitedby))
        os.makedirs(os.path.dirname(local_filename), exist_ok=True)
        if not os.path.isfile(local_filename):
            # remove info to save. can be recovery by using .fill()
            publication.author = publication.author.id
            publication.bib = None
            publication.filled = False
            with open(local_filename, 'wb') as f:
                pickle.dump(publication, f, pickle.HIGHEST_PROTOCOL)


def publications_is_saved(publication: Publication):
    """
    Check if publications is already saved
    :param publication:
    :return:
    """
    if publication is not None and hasattr(publication, 'id_scholarcitedby'):
        local_filename = os.path.join(path_to_publications, '{}.pkl'.format(publication.id_scholarcitedby))
        return os.path.isfile(local_filename)
    return False


def save_pending_citations(citations):
    """
    Save pending citations for future queries (Example: captcha error requires treatment)
    :param citations:
    :return:
    """
    with open(pending_citations_file, 'wb') as f:
        pickle.dump(citations, f, pickle.HIGHEST_PROTOCOL)


def load_pending_citations():
    """
    Load pending citations
    :return:
    """
    citations = list()
    if os.path.isfile(pending_citations_file):
        with open(pending_citations_file, 'rb') as f:
            citations = pickle.load(f)
    return citations


def search_citations(publications, pubs_author=None, related_publications=None):
    if related_publications is None:
        related_publications = list()

    print()
    for pub in publications:
        pub = ExtendedPublication(pub)
        if not pub.filled:
            pub.fill()
        if pub.author is None:
            if pubs_author is not None:
                pub.author = pubs_author
            else:
                pub.fill_author()

        # Check if publication was saved
        if publications_is_saved(pub):
            continue

        print("----- {} -----".format(pub.bib['title']))

        # Which papers cited that publication?
        print("Cited by")
        citations = pub.get_citedby()
        # print([citation.bib['title'] for citation in pub.get_citedby()])

        count = 0
        for citation in citations:
            if hasattr(citation, 'id_scholarcitedby'):
                print(citation.bib['title'])
                print(citation.id_scholarcitedby)
                pub.cited_in.append(citation.id_scholarcitedby)
                # citation = ExtendedPublication(citation)
                # citation.fill_author()
                # save_publication(copy(citation))

                related_publications.append(citation)

            count += 1
            if 0 < limit_citations <= count:
                break

        # Save publication
        save_publication(copy(pub))

        if len(related_publications) > 0:
            # Temp save the list of related publications (citations)
            save_pending_citations(related_publications)

    if len(related_publications) > 0:
        print()
        print("Looking Citations")
        search_citations(related_publications)


if __name__=='__main__':
    print("Searching")
    # Retrieve the author's data, fill-in, and print
    # search_query = scholarly.search_author('Barabasi')
    # search_query = scholarly.search_author('Peter Norvig')
    search_query = scholarly.search_author('Christopher D Manning')
    query_author = next(search_query).fill()
    print("Author")
    print(query_author.name)
    print(query_author.interests)
    print(len(query_author.publications))

    save_author(copy(query_author))

    # Print the titles of the author's publications
    print("Publications")
    print([pub.bib['title'] for pub in query_author.publications])

    search_citations(query_author.publications, pubs_author=query_author, related_publications=load_pending_citations())

    if os.path.isfile(pending_citations_file):
        os.remove(pending_citations_file)
