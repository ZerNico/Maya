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

package extraction

import (
	"github.com/ZerNico/Maya/go_bot/modules/users"
	"github.com/ZerNico/Maya/go_bot/modules/utils/error_handling"
	"github.com/PaulSonOfLars/gotgbot/ext"
	"github.com/google/uuid"
	"strconv"
	"strings"
	"unicode"
)

func IdFromReply(m *ext.Message) (int, string) {
	prevMessage := m.ReplyToMessage
	if prevMessage == nil {
		return 0, ""
	}
	userId := prevMessage.From.Id
	res := strings.SplitN(m.Text, " ", 2)
	if len(res) < 2 {
		return userId, ""
	}
	return userId, res[1]
}

func ExtractUserAndText(m *ext.Message, args []string) (int, string) {
	prevMessage := m.ReplyToMessage
	splitText := strings.SplitN(m.Text, " ", 2)

	if len(splitText) < 2 {
		return IdFromReply(m)
	}

	textToParse := splitText[1]

	text := ""

	var userId int
	accepted := make(map[string]struct{})
	accepted["text_mention"] = struct{}{}

	entities := m.ParseEntityTypes(accepted)

	var ent *ext.ParsedMessageEntity
	var isId = false
	if len(entities) > 0 {
		ent = &entities[0]
	} else {
		ent = nil
	}

	if entities != nil && ent != nil && ent.Offset == (len(m.Text)-len(textToParse)) {
		ent = &entities[0]
		userId = ent.User.Id
		text = strconv.Itoa(int(m.Text[ent.Offset+ent.Length]))
	} else if len(args) >= 1 && args[0][0] == '@' {
		user := args[0]
		userId = users.GetUserId(user)
		if userId == 0 {
			_, err := m.ReplyText("I don't have that user in my db. You'll be able to interact with them if you reply to that person's message instead, or forward one of that user's messages.")
			error_handling.HandleErr(err)
			return 0, ""
		} else {
			res := strings.SplitN(m.Text, " ", 3)
			if len(res) >= 3 {
				text = res[2]
			}
		}
	} else if len(args) >= 1 {
		isId = true
		for _, arg := range args[0] {
			if unicode.IsDigit(arg) {
				continue
			} else {
				isId = false
				break
			}
		}
		if isId {
			userId, _ = strconv.Atoi(args[0])
			res := strings.SplitN(m.Text, " ", 3)
			if len(res) >= 3 {
				text = res[2]
			}
		}
	}
	if !isId && prevMessage != nil {
		_, parseErr := uuid.Parse(args[0])
		userId, text = IdFromReply(m)
		if parseErr == nil {
			return userId, text
		}
	} else if !isId {
		_, parseErr := uuid.Parse(args[0])
		if parseErr == nil {
			return userId, text
		}
	}

	_, err := m.Bot.GetChat(userId)
	if err != nil {

		_, err := m.ReplyText("I don't seem to have interacted with this user before - please forward a message from " +
			"them to give me control! (like a voodoo doll, I need a piece of them to be able " +
			"to execute certain commands...)")
		error_handling.HandleErr(err)
		return 0, ""
	}
	return userId, text
}

func ExtractUser(message *ext.Message, args []string) int {
	userId, _ := ExtractUserAndText(message, args)
	return userId
}

func ExtractText(message *ext.Message) string {
	if message.Text != "" {
		return message.Text
	} else if message.Caption != "" {
		return message.Caption
	} else if message.Sticker != nil {
		return message.Sticker.Emoji
	} else {
		return ""
	}
}
