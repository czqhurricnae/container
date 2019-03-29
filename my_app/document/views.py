from flask import render_template, request, jsonify
from my_app.document import documents_blueprint as documents
import jieba
from functools import reduce

@documents.route('/document/', methods=['GET', 'POST'])
def post():
    if request.is_xhr:
        query = request.args.get('search')
        from ..models import Document
        seg_list = jieba.cut(sentence=query)
        ars_list = []
        for seg in seg_list:
            documents = Document.query.whoosh_search(seg, or_=True).all()
            if len(documents) != 0:
                ars_list.append(documents)
        try:
            document_set = reduce(
                lambda x, y: set(x).intersection(
                    set(y)), ars_list)
        except TypeError:
            document_set = []

        result = {}
        result[u'documents'] = []
        if len(document_set) != 0:
            for document in document_set:
                meta_information = dict()
                meta_information[u'title'] = document.title
                meta_information[u'url'] = document.get_url
                meta_information[u'model'] = document.model
                meta_information[u'chapter'] = document.chapter
                meta_information[u'office'] = document.office
                meta_information[u'date'] = document.date
                result[u'documents'].append(meta_information)
            if len(result[u'documents']):
                return jsonify(result=result)
        else:
            return jsonify(result=result)
    return render_template('document.html')


@documents.route('/document/<title>', methods=['GET', 'POST'])
def document_by_title(title):
    query = title
    print(query)
    from ..models import Document
    documents = Document.query.filter_by(title=query).all()
    print documents
    return render_template('document_by_title.html')


@documents.app_template_filter('change')
def change(string):
    return(string.replace('\\', '/'))
