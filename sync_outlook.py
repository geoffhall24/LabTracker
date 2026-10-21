import os
import sqlite3
import sys

if sys.platform != "win32":
  print("This script must be run on your local Windows PC.")
  sys.exit()

import pythoncom
import win32com.client

DB_FILE = "lab_queue.db"


def sync_outlook_emails():
  pythoncom.CoInitialize()
  outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, rga_number, notification_number, customer_name, notes FROM"
      " queue"
  )
  rows = cursor.fetchall()

  print("🔍 Scanning Outlook Inbox...")
  inbox = outlook.GetDefaultFolder(6)
  messages = inbox.Items
  messages.Sort("[ReceivedTime]", True)

  matched_inbox = 0
  for count, message in enumerate(messages):
    if count > 150:
      break
    try:
      sender = getattr(message, "SenderName", "")
      subject = getattr(message, "Subject", "")
      body = getattr(message, "Body", "")
      received_time = str(getattr(message, "ReceivedTime", ""))

      if (
          "return" in sender.lower()
          or "return" in subject.lower()
          or "returns" in subject.lower()
      ):
        for db_id, rga, notif, cust, existing_notes in rows:
          rga_str, notif_str = str(rga).strip(), str(notif).strip()
          if (rga_str and rga_str != "nan" and rga_str in subject) or (
              notif_str and notif_str != "nan" and notif_str in subject
          ):
            snippet = f"\n\n[Synced Email from Returns - {received_time}]\nSubject: {subject}\n{body[:1200]}"
            if snippet not in str(existing_notes or ""):
              cursor.execute(
                  "UPDATE queue SET notes = ? WHERE id = ?",
                  (str(existing_notes or "") + snippet, db_id),
              )
              matched_inbox += 1
    except Exception:
      continue

  print(f"✅ Added {matched_inbox} new inbox email(s) to database.")

  print("🔍 Scanning Outlook Sent Items...")
  sent_folder = outlook.GetDefaultFolder(5)
  sent_messages = sent_folder.Items
  sent_messages.Sort("[SentOn]", True)

  matched_sent = 0
  for count, message in enumerate(sent_messages):
    if count > 150:
      break
    try:
      subject = getattr(message, "Subject", "")
      body = getattr(message, "Body", "")
      sent_time = str(getattr(message, "SentOn", ""))
      to_recipient = getattr(message, "To", "")

      for db_id, rga, notif, cust, existing_notes in rows:
        rga_str, notif_str = str(rga).strip(), str(notif).strip()
        if (rga_str and rga_str != "nan" and rga_str in subject) or (
            notif_str and notif_str != "nan" and notif_str in subject
        ):
          snippet = f"\n\n[Synced Sent Reply - {sent_time}]\nTo: {to_recipient}\nSubject: {subject}\n{body[:1200]}"
          if "[Synced Sent Reply]" not in str(existing_notes or ""):
            cursor.execute(
                "UPDATE queue SET notes = ? WHERE id = ?",
                (str(existing_notes or "") + snippet, db_id),
            )
            matched_sent += 1
    except Exception:
      continue

  conn.commit()
  conn.close()
  print(f"✅ Added {matched_sent} new sent reply(s) to database.")
  print("🎉 Email synchronization complete!")


if __name__ == "__main__":
  sync_outlook_emails()