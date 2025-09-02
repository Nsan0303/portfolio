def edit_article(article_id):
    """記事編集画面を表示"""
    article = next((a for a in Blog_List if a['ID'] == article_id), None)
    if not article:
        return "記事が見つかりません", 404
    return f'''
    <form method="POST">
        <input type="text" name="title" value="{article['Title']}">
        <textarea name="description">{article['Description']}</textarea>
        <button type="submit">更新</button>
    </form>
    '''
