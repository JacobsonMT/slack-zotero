# --group and --api refer to Zotero
# The rest of the options are for the Slack-webhook (or Slack-compatible Zulip-webhook)
python3 slack-zotero.py --group 1966 \
                            --api "SECRET_^_^_KEY" \
    --webhook "https://frost.zulipchat.com/api/v1/external/slack_incoming?api_key=ALSO_SECRET_^_^_KEY&stream=zotero" \
                            --since 0 \
                            --username "Zotero Bot" \
                            --icon ":book:" \
                            --artifact "slack-zotero-bot-previous.json" \
                            -v

