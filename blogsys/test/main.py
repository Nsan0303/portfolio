import os


def create_draft():
    #ドラフト作成システム
    #ここにドラフトを作成するためのコードを追加
    import new_article
    new_article.main()

def upload_article():
    #記事アップロードシステム
    import upload
    upload.upload_article()

def delete_article():
    #記事削除システム
    import delete
    delete.delete_article()


print("Please enter the number of task you want to perform: \n1.create drafts file\n2.upload article\n3.delete article\nPlease select a task:and enter one of 1, 2, 3")


execution_choice = input().strip()

if execution_choice == "1":
    create_draft()
elif execution_choice == "2":
    upload_article()
elif execution_choice == "3":
    delete_article()
else:
    print("Invalid choice.")

