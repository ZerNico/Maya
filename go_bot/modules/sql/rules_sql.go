package sql

import (
	"encoding/json"
	"fmt"

	"github.com/ZerNico/Maya/go_bot/modules/utils/caching"
	"github.com/ZerNico/Maya/go_bot/modules/utils/error_handling"
)

type Rules struct {
	ChatId string `gorm:"primary_key" json:"chat_id"`
	Rules  string `json:"rules"`
}

func GetChatRules(chatId string) *Rules {
	ruleJson, err := caching.CACHE.Get(fmt.Sprintf("rules_%v", chatId))
	if err != nil {
		go cacheRules(chatId)
		return nil
	}

	var rules *Rules
	_ = json.Unmarshal(ruleJson, &rules)
	return rules
}

func SetChatRules(chatId, rules string) {
	defer func(chatId string) {
		go cacheRules(chatId)
	}(chatId)

	SESSION.Save(&Rules{ChatId: chatId, Rules: rules})
}

func cacheRules(chatId string) {
	rules := &Rules{}
	SESSION.Where("chat_id = ?", chatId).Find(&rules)
	ruleJson, _ := json.Marshal(&rules)
	err := caching.CACHE.Set(fmt.Sprintf("rules_%v", chatId), ruleJson)
	error_handling.HandleErr(err)
}
