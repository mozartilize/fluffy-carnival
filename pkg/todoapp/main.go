package main

import (
	"net/http"
	"time"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"

	_ "github.com/go-sql-driver/mysql"
	"github.com/jmoiron/sqlx"
	nullable "gopkg.in/guregu/null.v4"
)

// CustomContext Comment
type CustomContext struct {
	echo.Context
	db *sqlx.DB
}

// User user
type User struct {
	ID        uint64          `db:"id"`
	FirstName nullable.String `db:"first_name"`
	LastName  nullable.String `db:"last_name"`
	Email     nullable.String `db:"email"`
	CreatedAt time.Time       `db:"created_at"`
}

func main() {
	// Echo instance
	db, err := sqlx.Open("mysql", "test:pwd@/test?parseTime=true")
	if err != nil {
		panic(err)
	}

	db.SetConnMaxLifetime(time.Minute * 3)
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)

	e := echo.New()
	e.Use(func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			cc := &CustomContext{c, db}
			return next(cc)
		}
	})

	// Middleware
	e.Use(middleware.Logger())
	e.Use(middleware.Recover())

	// Routes
	e.GET("/users", users)

	// Start server
	e.Logger.Fatal(e.Start(":1323"))
}

// Handler
func users(c echo.Context) error {
	cc := c.(*CustomContext)
	db := cc.db
	users := []User{}
	error := db.Select(&users, "select id, first_name, last_name, email, created_at from portal_auth_users")
	if error != nil {
		panic(error)
	}
	return c.JSON(http.StatusOK, users)
}
