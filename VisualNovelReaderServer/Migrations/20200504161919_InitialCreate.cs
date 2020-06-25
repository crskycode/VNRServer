using System;
using Microsoft.EntityFrameworkCore.Migrations;

namespace VisualNovelReaderServer.Migrations
{
    public partial class InitialCreate : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "TextSetting",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    Language = table.Column<string>(nullable: true),
                    Encoding = table.Column<string>(nullable: true),
                    KeepAllText = table.Column<bool>(nullable: false),
                    KeepSpaces = table.Column<bool>(nullable: false),
                    RemoveRepeat = table.Column<bool>(nullable: false),
                    IgnoreRepeat = table.Column<bool>(nullable: false),
                    HookCode = table.Column<string>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_TextSetting", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "User",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    Permissions = table.Column<int>(nullable: false),
                    Username = table.Column<string>(nullable: true),
                    Password = table.Column<string>(nullable: true),
                    Email = table.Column<string>(nullable: true),
                    ExtraInfo = table.Column<string>(nullable: true),
                    Language = table.Column<string>(nullable: true),
                    Gender = table.Column<string>(nullable: true),
                    Avatar = table.Column<string>(nullable: true),
                    HomePage = table.Column<string>(nullable: true),
                    Color = table.Column<string>(nullable: true),
                    CreationTime = table.Column<DateTime>(nullable: false),
                    AccessTime = table.Column<DateTime>(nullable: false),
                    ModifiedTime = table.Column<DateTime>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_User", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "TextHook",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    Type = table.Column<string>(nullable: true),
                    Name = table.Column<string>(nullable: true),
                    Sig = table.Column<string>(nullable: true),
                    TextSettingId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_TextHook", x => x.Id);
                    table.ForeignKey(
                        name: "FK_TextHook_TextSetting_TextSettingId",
                        column: x => x.TextSettingId,
                        principalTable: "TextSetting",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "GameItem",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    Title = table.Column<string>(nullable: true),
                    RomajiTitle = table.Column<string>(nullable: true),
                    Brand = table.Column<string>(nullable: true),
                    Series = table.Column<string>(nullable: true),
                    ImageUrl = table.Column<string>(nullable: true),
                    BannerUrl = table.Column<string>(nullable: true),
                    Wiki = table.Column<string>(nullable: true),
                    FileSize = table.Column<long>(nullable: false),
                    Tags = table.Column<string>(nullable: true),
                    Date = table.Column<string>(nullable: true),
                    Artists = table.Column<string>(nullable: true),
                    SdArtists = table.Column<string>(nullable: true),
                    Writers = table.Column<string>(nullable: true),
                    Musicians = table.Column<string>(nullable: true),
                    Otome = table.Column<bool>(nullable: false),
                    Ecchi = table.Column<bool>(nullable: false),
                    Okazu = table.Column<bool>(nullable: false),
                    TopicCount = table.Column<int>(nullable: false),
                    AnnotCount = table.Column<int>(nullable: false),
                    SubtitleCount = table.Column<int>(nullable: false),
                    PlayUserCount = table.Column<int>(nullable: false),
                    ScapeMedian = table.Column<int>(nullable: false),
                    ScapeCount = table.Column<int>(nullable: false),
                    OverallScoreCount = table.Column<int>(nullable: false),
                    OverallScoreSum = table.Column<int>(nullable: false),
                    EcchiScoreCount = table.Column<int>(nullable: false),
                    EcchiScoreSum = table.Column<int>(nullable: false),
                    CreatorId = table.Column<int>(nullable: false),
                    CreationTime = table.Column<DateTime>(nullable: false),
                    ModifiedTime = table.Column<DateTime>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_GameItem", x => x.Id);
                    table.ForeignKey(
                        name: "FK_GameItem_User_CreatorId",
                        column: x => x.CreatorId,
                        principalTable: "User",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Game",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    Md5 = table.Column<string>(nullable: true),
                    GameItemId = table.Column<int>(nullable: true),
                    TextSettingId = table.Column<int>(nullable: false),
                    CreatorId = table.Column<int>(nullable: false),
                    CreationTime = table.Column<DateTime>(nullable: false),
                    ModifiedTime = table.Column<DateTime>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Game", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Game_User_CreatorId",
                        column: x => x.CreatorId,
                        principalTable: "User",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Game_GameItem_GameItemId",
                        column: x => x.GameItemId,
                        principalTable: "GameItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Game_TextSetting_TextSettingId",
                        column: x => x.TextSettingId,
                        principalTable: "TextSetting",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Comment",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    GameId = table.Column<int>(nullable: false),
                    GameItemId = table.Column<int>(nullable: true),
                    Context_Hash = table.Column<string>(nullable: true),
                    Context_Size = table.Column<int>(nullable: true),
                    Context_Content = table.Column<string>(nullable: true),
                    Type = table.Column<string>(nullable: true),
                    Language = table.Column<string>(nullable: true),
                    Text = table.Column<string>(nullable: true),
                    Disabled = table.Column<bool>(nullable: false),
                    Locked = table.Column<bool>(nullable: false),
                    Deleted = table.Column<bool>(nullable: false),
                    Liked = table.Column<int>(nullable: false),
                    Disliked = table.Column<int>(nullable: false),
                    CreatorId = table.Column<int>(nullable: false),
                    CreationComment = table.Column<string>(nullable: true),
                    CreationTime = table.Column<DateTime>(nullable: false),
                    EditorId = table.Column<int>(nullable: true),
                    RevisionComment = table.Column<string>(nullable: true),
                    RevisionTime = table.Column<DateTime>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Comment", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Comment_User_CreatorId",
                        column: x => x.CreatorId,
                        principalTable: "User",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Comment_User_EditorId",
                        column: x => x.EditorId,
                        principalTable: "User",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Comment_Game_GameId",
                        column: x => x.GameId,
                        principalTable: "Game",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Comment_GameItem_GameItemId",
                        column: x => x.GameItemId,
                        principalTable: "GameItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "GameName",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    Type = table.Column<string>(nullable: true),
                    Value = table.Column<string>(nullable: true),
                    GameId = table.Column<int>(nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_GameName", x => x.Id);
                    table.ForeignKey(
                        name: "FK_GameName_Game_GameId",
                        column: x => x.GameId,
                        principalTable: "Game",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Reference",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    Type = table.Column<string>(nullable: true),
                    GameId = table.Column<int>(nullable: false),
                    GameItemId = table.Column<int>(nullable: false),
                    Title = table.Column<string>(nullable: true),
                    Brand = table.Column<string>(nullable: true),
                    Date = table.Column<DateTime>(nullable: false),
                    Key = table.Column<string>(nullable: true),
                    Url = table.Column<string>(nullable: true),
                    CreatorId = table.Column<int>(nullable: false),
                    CreationTime = table.Column<DateTime>(nullable: false),
                    ModifiedTime = table.Column<DateTime>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Reference", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Reference_User_CreatorId",
                        column: x => x.CreatorId,
                        principalTable: "User",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Reference_Game_GameId",
                        column: x => x.GameId,
                        principalTable: "Game",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Reference_GameItem_GameItemId",
                        column: x => x.GameItemId,
                        principalTable: "GameItem",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Term",
                columns: table => new
                {
                    Id = table.Column<int>(nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    FromLanguage = table.Column<string>(nullable: true),
                    ToLanguage = table.Column<string>(nullable: true),
                    Type = table.Column<string>(nullable: true),
                    Translators = table.Column<string>(nullable: true),
                    ContextType = table.Column<string>(nullable: true),
                    GameId = table.Column<int>(nullable: true),
                    IsSpecial = table.Column<bool>(nullable: false),
                    IsPrivate = table.Column<bool>(nullable: false),
                    IsHentai = table.Column<bool>(nullable: false),
                    IsRegex = table.Column<bool>(nullable: false),
                    IsPhrase = table.Column<bool>(nullable: false),
                    IgnoreCase = table.Column<bool>(nullable: false),
                    Disabled = table.Column<bool>(nullable: false),
                    Deleted = table.Column<bool>(nullable: false),
                    Priority = table.Column<int>(nullable: false),
                    Role = table.Column<string>(nullable: true),
                    Pattern = table.Column<string>(nullable: true),
                    Text = table.Column<string>(nullable: true),
                    Ruby = table.Column<string>(nullable: true),
                    CreatorId = table.Column<int>(nullable: false),
                    CreationComment = table.Column<string>(nullable: true),
                    CreationTime = table.Column<DateTime>(nullable: false),
                    EditorId = table.Column<int>(nullable: true),
                    RevisionComment = table.Column<string>(nullable: true),
                    RevisionTime = table.Column<DateTime>(nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Term", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Term_User_CreatorId",
                        column: x => x.CreatorId,
                        principalTable: "User",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Term_User_EditorId",
                        column: x => x.EditorId,
                        principalTable: "User",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Term_Game_GameId",
                        column: x => x.GameId,
                        principalTable: "Game",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Comment_CreatorId",
                table: "Comment",
                column: "CreatorId");

            migrationBuilder.CreateIndex(
                name: "IX_Comment_EditorId",
                table: "Comment",
                column: "EditorId");

            migrationBuilder.CreateIndex(
                name: "IX_Comment_GameId",
                table: "Comment",
                column: "GameId");

            migrationBuilder.CreateIndex(
                name: "IX_Comment_GameItemId",
                table: "Comment",
                column: "GameItemId");

            migrationBuilder.CreateIndex(
                name: "IX_Game_CreatorId",
                table: "Game",
                column: "CreatorId");

            migrationBuilder.CreateIndex(
                name: "IX_Game_GameItemId",
                table: "Game",
                column: "GameItemId");

            migrationBuilder.CreateIndex(
                name: "IX_Game_TextSettingId",
                table: "Game",
                column: "TextSettingId");

            migrationBuilder.CreateIndex(
                name: "IX_GameItem_CreatorId",
                table: "GameItem",
                column: "CreatorId");

            migrationBuilder.CreateIndex(
                name: "IX_GameName_GameId",
                table: "GameName",
                column: "GameId");

            migrationBuilder.CreateIndex(
                name: "IX_Reference_CreatorId",
                table: "Reference",
                column: "CreatorId");

            migrationBuilder.CreateIndex(
                name: "IX_Reference_GameId",
                table: "Reference",
                column: "GameId");

            migrationBuilder.CreateIndex(
                name: "IX_Reference_GameItemId",
                table: "Reference",
                column: "GameItemId");

            migrationBuilder.CreateIndex(
                name: "IX_Term_CreatorId",
                table: "Term",
                column: "CreatorId");

            migrationBuilder.CreateIndex(
                name: "IX_Term_EditorId",
                table: "Term",
                column: "EditorId");

            migrationBuilder.CreateIndex(
                name: "IX_Term_GameId",
                table: "Term",
                column: "GameId");

            migrationBuilder.CreateIndex(
                name: "IX_TextHook_TextSettingId",
                table: "TextHook",
                column: "TextSettingId");
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Comment");

            migrationBuilder.DropTable(
                name: "GameName");

            migrationBuilder.DropTable(
                name: "Reference");

            migrationBuilder.DropTable(
                name: "Term");

            migrationBuilder.DropTable(
                name: "TextHook");

            migrationBuilder.DropTable(
                name: "Game");

            migrationBuilder.DropTable(
                name: "GameItem");

            migrationBuilder.DropTable(
                name: "TextSetting");

            migrationBuilder.DropTable(
                name: "User");
        }
    }
}
