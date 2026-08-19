using Telegram.Bot;
using Telegram.Bot.Types;
using Telegram.Bot.Types.Enums;

public class MemeBot : TelegramBotClient
{
    public MemeBot(string token) : base(token)
    {
        OnMessage += MessageEcho;
    }

    async Task MessageEcho(Message msg, UpdateType type)
    {
        if (msg.Text is null) return;

        await this.SendMessage(msg.Chat, "you said: " + msg.Text);
    }
}