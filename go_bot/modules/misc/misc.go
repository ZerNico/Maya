/*
 *   Copyright 2019 ATechnoHazard  <amolele@gmail.com>
 *
 *   Permission is hereby granted, free of charge, to any person obtaining a copy
 *   of this software and associated documentation files (the "Software"), to deal
 *   in the Software without restriction, including without limitation the rights
 *   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 *   copies of the Software, and to permit persons to whom the Software is
 *   furnished to do so, subject to the following conditions:
 *
 *   The above copyright notice and this permission notice shall be included in all
 *   copies or substantial portions of the Software.
 *
 *   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 *   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 *   SOFTWARE.
 */

package misc

import (
	"fmt"
	"html"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/ZerNico/Maya/go_bot"
	"github.com/ZerNico/Maya/go_bot/modules/sql"
	"github.com/ZerNico/Maya/go_bot/modules/utils/caching"
	"github.com/ZerNico/Maya/go_bot/modules/utils/error_handling"
	"github.com/ZerNico/Maya/go_bot/modules/utils/extraction"
	"github.com/ZerNico/Maya/go_bot/modules/utils/helpers"

	"github.com/PaulSonOfLars/gotgbot"
	"github.com/PaulSonOfLars/gotgbot/ext"
	"github.com/PaulSonOfLars/gotgbot/handlers"
	"github.com/sirupsen/logrus"
	"github.com/tcnksm/go-httpstat"
)

func getId(bot ext.Bot, u *gotgbot.Update, args []string) error {
	userId := extraction.ExtractUser(u.EffectiveMessage, args)
	if userId != 0 {
		if u.EffectiveMessage.ReplyToMessage != nil && u.EffectiveMessage.ReplyToMessage.ForwardFrom != nil {
			user1 := u.EffectiveMessage.ReplyToMessage.From
			user2 := u.EffectiveMessage.ReplyToMessage.ForwardFrom
			_, err := u.EffectiveMessage.ReplyHTMLf("The original sender, %v, has an ID of <code>%v</code>.\n"+
				"The forwarder, %v, has an ID of <code>%v</code>.", html.EscapeString(user2.FirstName),
				user2.Id,
				html.EscapeString(user1.FirstName),
				user1.Id)
			return err
		} else {
			user, err := bot.GetChat(userId)
			error_handling.HandleErr(err)
			_, err = u.EffectiveMessage.ReplyHTMLf("%v's ID is <code>%v</code>", html.EscapeString(user.FirstName), user.Id)
		}
	} else {
		chat := u.EffectiveChat
		if chat.Type == "private" {
			_, err := u.EffectiveMessage.ReplyHTMLf("Your ID is <code>%v</code>", chat.Id)
			return err
		} else {
			_, err := u.EffectiveMessage.ReplyHTMLf("This group's ID is <code>%v</code>", chat.Id)
			return err
		}
	}
	return nil
}

func info(bot ext.Bot, u *gotgbot.Update, args []string) error {
	msg := u.EffectiveMessage
	chat := u.EffectiveChat
	userId := extraction.ExtractUser(msg, args)
	var user *ext.User

	if userId != 0 {
		userChat, _ := bot.GetChat(userId)
		user = &ext.User{
			Id:        userChat.Id,
			FirstName: userChat.FirstName,
			LastName:  userChat.LastName,
		}

	} else if msg.ReplyToMessage == nil && len(args) <= 0 {
		user = msg.From
		userId = msg.From.Id

	} else if _, err := strconv.Atoi(args[0]); msg.ReplyToMessage == nil && (len(args) <= 0 || (len(args) >= 1 && strings.HasPrefix(args[0], "@") && err != nil && msg.ParseEntities()[0].Type != "TEXT_MENTION")) {
		_, err := msg.ReplyText("Yeah nah, this mans doesn't exist.")
		return err
	} else {
		return nil
	}

	text := fmt.Sprintf("<b>User info</b>"+
		"\nID: <code>%v</code>"+
		"\nFirst Name: %v", userId, html.EscapeString(user.FirstName))

	if user.LastName != "" {
		text += fmt.Sprintf("\nLast Name: %v", user.LastName)
	}

	if user.Username != "" {
		text += fmt.Sprintf("\nUsername: @%v", user.Username)
	}

	text += fmt.Sprintf("\nPermanent user link: %v", helpers.MentionHtml(user.Id, user.FirstName+user.LastName))

	fed := sql.GetChatFed(strconv.Itoa(chat.Id))
	if fed != nil {
		fban := sql.GetFbanUser(fed.Id, strconv.Itoa(userId))
		if fban != nil {
			text += fmt.Sprintf("\n\nThis user is fedbanned in the current federation - "+
				"<code>%v</code>", fed.FedName)
		} else {
			text += "\n\nThis user is not fedbanned in the current federation."
		}
	}

	if user.Id == go_bot.BotConfig.OwnerId {
		text += "\n\nDis nibba stronk af!"
	} else {
		for _, id := range go_bot.BotConfig.SudoUsers {
			if strconv.Itoa(user.Id) == id {
				text += "\n\nThis person is one of my sudo users! " +
					"Nearly as powerful as my owner - so watch it."
			}
		}
	}
	_, err := u.EffectiveMessage.ReplyHTML(text)
	return err
}

func ping(_ ext.Bot, u *gotgbot.Update) error {
	user := u.EffectiveUser

	sudos := go_bot.BotConfig.SudoUsers
	sudos = append(sudos, strconv.Itoa(go_bot.BotConfig.OwnerId))

	if !helpers.Contains(sudos, strconv.Itoa(user.Id)) {
		return nil
	}

	req, err := http.NewRequest("GET", "https://google.com", nil)
	error_handling.HandleErr(err)

	var result httpstat.Result
	ctx := httpstat.WithHTTPStat(req.Context(), &result)
	req = req.WithContext(ctx)

	client := http.DefaultClient
	res, err := client.Do(req)
	error_handling.HandleErr(err)

	if _, err := io.Copy(ioutil.Discard, res.Body); err != nil {
		logrus.Println(err)
	}

	_ = res.Body.Close()

	text := fmt.Sprintf("Ping: <b>%d</b> ms", result.ServerProcessing/time.Millisecond)

	_, err = u.EffectiveMessage.ReplyHTML(text)
	return err
}

func clearCache(_ ext.Bot, u *gotgbot.Update) error {
	user := u.EffectiveUser
	msg := u.EffectiveMessage

	sudos := go_bot.BotConfig.SudoUsers
	sudos = append(sudos, strconv.Itoa(go_bot.BotConfig.OwnerId))

	if !helpers.Contains(sudos, strconv.Itoa(user.Id)) {
		return nil
	}

	err := caching.CACHE.Reset()
	if err != nil {
		_, err = msg.ReplyText("Cache couldn't be cleared!")
		return err
	}

	_, err = msg.ReplyText("Cache has been cleared.")
	return err
}

func LoadMisc(u *gotgbot.Updater) {
	defer log.Println("Loading module misc")
	u.Dispatcher.AddHandler(handlers.NewPrefixArgsCommand("id", []rune{'/', '!'}, getId))
	u.Dispatcher.AddHandler(handlers.NewPrefixArgsCommand("info", []rune{'/', '!'}, info))
	u.Dispatcher.AddHandler(handlers.NewPrefixCommand("ping", []rune{'/', '!'}, ping))
	u.Dispatcher.AddHandler(handlers.NewPrefixCommand("clearcache", []rune{'/', '!'}, clearCache))
}
